# base_health.py
"""
현재 생활습관 입력 & 단기 예측 페이지 (루트 배치용)

역할
- 사용자가 오늘 생활습관/지표를 입력
- 입력값을 data/follow_sample.csv 에 누적 저장 (T_ID=1 고정, 공란은 io_utils.append_row에서 -1 처리)
- 방금 저장한 1행(또는 마지막 1행)으로 단기 예측 수행 (base_model_* 또는 current_model_* 있을 때)

필요 모듈
- utils.io_utils: append_row, load_df
- utils.preprocess: preprocess_base
- utils.model_utils: load_models(kind="base" | "current")
"""

import streamlit as st
import pandas as pd
from datetime import date

from utils.io_utils import append_row, load_df
from utils.preprocess import preprocess_base
from utils.model_utils import load_models


def render(go_home):
    st.title("📌 현재 생활습관 기반 만성질환 예측기")
    st.write("👉 오늘 입력한 생활습관/신체지표를 저장하고, 단기 예측 결과를 확인합니다.")

    if st.button("⬅ 홈으로 돌아가기"):
        go_home()

    st.divider()

    # -------------------------------
    # 입력 폼
    # -------------------------------
    with st.form("daily_input_form", clear_on_submit=False):
        st.subheader("📝 생활습관 및 신체지표 입력")
        
        # 필수 항목 섹션
        st.markdown("### 🔴 필수 입력 항목")
        st.info("아래 항목들은 반드시 입력해주세요.")
        
        colA, colB = st.columns(2)
        
        with colA:
            st.markdown("**기본 정보**")
            EDATE = st.date_input("📅 조사일 (EDATE)", value=date.today())
            CHILD_sel = st.selectbox("🤱 임신/출산 경험 (CHILD)", ["선택", 0, 1])
            SEX_sel = st.selectbox("👤 성별 (SEX)", ["선택", 1, 2])
            EDU = st.number_input("🎓 교육수준 (EDU)", min_value=0, step=1)
            T_AGE = st.number_input("🎂 나이 (T_AGE)", min_value=0, step=1)
        
        with colB:
            st.markdown("**생활습관 & 기존 질환**")
            T_DRINK_sel = st.selectbox("🍺 오늘 음주여부 (T_DRINK)", ["선택", 0, 1])
            T_SMOKE_sel = st.selectbox("🚬 오늘 흡연여부 (T_SMOKE)", ["선택", 0, 1])
            HTN_sel = st.selectbox("🩺 기존 고혈압 (HTN)", ["선택", 0, 1])
            DM_sel = st.selectbox("🍯 기존 당뇨병 (DM)", ["선택", 0, 1])
            LIP_sel = st.selectbox("🩸 기존 고지혈증 (LIP)", ["선택", 0, 1])
        
        st.markdown("**신체지표**")
        colC, colD = st.columns(2)
        with colC:
            WEIGHT = st.number_input("⚖️ 체중 (WEIGHT) - kg", min_value=0.0, step=0.1)
        with colD:
            HEIGHT = st.number_input("📏 신장 (HEIGHT) - cm", min_value=0.0, step=0.1)
        
        st.divider()
        
        # 선택 항목 섹션
        st.markdown("### 🟡 선택 입력 항목")
        st.info("아래 항목들은 선택사항입니다. 모르는 경우 입력하지 않으셔도 됩니다.")
        
        colE, colF, colG = st.columns(3)
        
        with colE:
            st.markdown("**추가 개인정보**")
            MNSAG = st.number_input("🌙 초경나이 (MNSAG)", min_value=-1, step=1, value=-1)
            SMAG = st.number_input("🚬 흡연 시작 나이 (SMAG)", min_value=-1, step=1, value=-1)
            
        with colF:
            st.markdown("**가족력**")
            FMMHT = st.number_input("👩 고혈압 엄마 (FMMHT)", min_value=-1, max_value=1, step=1, value=-1)
            FMFHT = st.number_input("👨 고혈압 아빠 (FMFHT)", min_value=-1, max_value=1, step=1, value=-1)
            FMMDM = st.number_input("👩 당뇨병 엄마 (FMMDM)", min_value=-1, max_value=1, step=1, value=-1)
            FMFDM = st.number_input("👨 당뇨병 아빠 (FMFDM)", min_value=-1, max_value=1, step=1, value=-1)
        
        with colG:
            st.markdown("**음주/흡연 상세**")
            T_DRINKAM = st.number_input("🍺 오늘 음주량 (T_DRINKAM)", min_value=-1.0, step=0.1, value=-1.0)
            T_SMOKEAM = st.number_input("🚬 오늘 흡연량 (T_SMOKEAM)", min_value=-1.0, step=0.1, value=-1.0)
        
        st.markdown("**신체 측정값**")
        colH, colI = st.columns(2)
        with colH:
            WAIST = st.number_input("📐 허리둘레 (WAIST) - cm", min_value=-1.0, step=0.1, value=-1.0)
            HIP = st.number_input("📐 엉덩이둘레 (HIP) - cm", min_value=-1.0, step=0.1, value=-1.0)
            SBP = st.number_input("💓 수축기 혈압 (SBP) - mmHg", min_value=-1.0, step=0.1, value=-1.0)
            DBP = st.number_input("💓 이완기 혈압 (DBP) - mmHg", min_value=-1.0, step=0.1, value=-1.0)
        with colI:
            PULSE = st.number_input("💗 맥박 (PULSE) - bpm", min_value=-1.0, step=0.1, value=-1.0)
            EXER = st.number_input("🏃 운동 빈도 (EXER)", min_value=-1.0, step=0.1, value=-1.0)

        st.markdown("**🔬 임상지표 (검사 결과)**")
        colJ, colK = st.columns(2)
        with colJ:
            HBA1C = st.number_input("🩸 당화혈색소 (HBA1C) - %", min_value=-1.0, step=0.01, value=-1.0)
            GLU = st.number_input("🍯 공복혈당 (GLU) - mg/dL", min_value=-1.0, step=0.1, value=-1.0)
            HOMAIR = st.number_input("⚡ 인슐린저항성 (HOMAIR)", min_value=-1.0, step=0.001, value=-1.0)
            TCHL = st.number_input("🩸 총콜레스테롤 (TCHL) - mg/dL", min_value=-1.0, step=0.1, value=-1.0)
        with colK:
            HDL = st.number_input("🩸 HDL콜레스테롤 (HDL) - mg/dL", min_value=-1.0, step=0.1, value=-1.0)
            TG = st.number_input("🩸 중성지방 (TG) - mg/dL", min_value=-1.0, step=0.1, value=-1.0)
            AST = st.number_input("🩸 AST (간기능) - U/L", min_value=-1.0, step=0.1, value=-1.0)
            ALT = st.number_input("🩸 ALT (간기능) - U/L", min_value=-1.0, step=0.1, value=-1.0)
            CREATININE = st.number_input("🩸 크레아티닌 (신장기능) - mg/dL", min_value=-1.0, step=0.01, value=-1.0)

        submitted = st.form_submit_button("💾 저장하고 단기 예측 실행")

    # -------------------------------
    # 저장 + 검증 + 단기 예측
    # -------------------------------
    if submitted:
        # 1) 필수값 검증
        errors = []
        CHILD = None if CHILD_sel == "선택" else CHILD_sel
        SEX   = None if SEX_sel   == "선택" else SEX_sel
        T_DRINK = None if T_DRINK_sel == "선택" else T_DRINK_sel
        T_SMOKE = None if T_SMOKE_sel == "선택" else T_SMOKE_sel
        HTN = None if HTN_sel == "선택" else HTN_sel
        DM  = None if DM_sel  == "선택" else DM_sel
        LIP = None if LIP_sel == "선택" else LIP_sel

        if EDATE is None:
            errors.append("EDATE(조사일)를 선택하세요.")
        if CHILD is None:
            errors.append("CHILD(임신/출산 경험)을 선택하세요.")
        if SEX is None:
            errors.append("SEX(성별)을 선택하세요.")
        if EDU is None or EDU < 0:
            errors.append("EDU(교육수준)를 올바르게 입력하세요.")
        if T_DRINK is None:
            errors.append("T_DRINK(오늘 음주여부)를 선택하세요.")
        if T_SMOKE is None:
            errors.append("T_SMOKE(오늘 흡연)를 선택하세요.")
        if T_AGE is None or T_AGE < 0:
            errors.append("T_AGE(나이)를 올바르게 입력하세요.")
        if HTN is None:
            errors.append("HTN(기존 고혈압)을 선택하세요.")
        if DM is None:
            errors.append("DM(기존 당뇨병)을 선택하세요.")
        if LIP is None:
            errors.append("LIP(기존 고지혈증)을 선택하세요.")
        if WEIGHT is None or WEIGHT <= 0:
            errors.append("WEIGHT(체중)을 0보다 크게 입력하세요.")
        if HEIGHT is None or HEIGHT <= 0:
            errors.append("HEIGHT(신장)을 0보다 크게 입력하세요.")

        if errors:
            for e in errors:
                st.error(e)
            st.stop()

        # 2) 저장할 행 구성 (선택 항목은 이미 -1 기본값)
        row = {
            "T_ID": 1,
            "EDATE": EDATE.isoformat() if isinstance(EDATE, (date, pd.Timestamp)) else EDATE,

            "CHILD": CHILD, "SEX": SEX, "MNSAG": MNSAG, "EDU": EDU, "SMAG": SMAG,
            "T_DRINK": T_DRINK, "T_DRINKAM": T_DRINKAM, "T_SMOKE": T_SMOKE, "T_SMOKEAM": T_SMOKEAM,
            "T_AGE": T_AGE,

            "HTN": HTN, "DM": DM, "LIP": LIP,
            "FMMHT": FMMHT, "FMFHT": FMFHT, "FMMDM": FMMDM, "FMFDM": FMFDM,

            "WEIGHT": WEIGHT, "HEIGHT": HEIGHT, "WAIST": WAIST, "HIP": HIP,
            "SBP": SBP, "DBP": DBP, "PULSE": PULSE, "EXER": EXER,

            "HBA1C": HBA1C, "GLU": GLU, "HOMAIR": HOMAIR,
            "TCHL": TCHL, "HDL": HDL, "TG": TG, "AST": AST, "ALT": ALT, "CREATININE": CREATININE,
        }

        try:
            # 3) CSV 저장
            append_row(row)
            st.success("저장 완료! data/follow_sample.csv 에 누적되었습니다.")

            # 4) 방금 저장한 1행 전처리
            df = load_df()
            if "T_ID" in df.columns:
                df["T_ID"] = pd.to_numeric(df["T_ID"], errors="coerce")
            df_user = df[df["T_ID"] == 1]
            last_row_df = df_user.tail(1)
            X = preprocess_base(last_row_df)

            # 5) 단기 예측 (base → current 순 폴백)
            models = None
            try:
                models = load_models(kind="base")
            except FileNotFoundError:
                try:
                    models = load_models(kind="current")
                except FileNotFoundError:
                    models = None

            if models is None:
                st.info("단기 예측용 모델(`base_model_*` 또는 `current_model_*`)이 없습니다.\n"
                        "→ 저장은 계속 누적됩니다. 10년 후 예측 페이지는 사용 가능합니다.")
            else:
                with st.spinner("단기 예측 실행 중..."):
                    st.subheader("⚡ 단기 예측 결과")
                    for disease_name, model in models.items():
                        prob = float(model.predict_proba(X)[0][1])
                        st.write(f"**{disease_name}**: {prob:.2%}")

            # 6) 최근 입력 미리보기
            with st.expander("📄 최근 입력(상위 5행) 보기"):
                st.dataframe(df_user.tail(5), use_container_width=True)

        except FileNotFoundError:
            st.error("데이터 파일을 찾을 수 없습니다. data/follow_sample.csv 경로를 확인하세요.")
        except Exception as e:
            st.error(f"에러 발생: {e}")
