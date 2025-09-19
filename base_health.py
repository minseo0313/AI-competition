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
        st.subheader("📝 오늘 입력")

        colA, colB, colC, colD = st.columns(4)

        # 필수: EDATE, CHILD, SEX, EDU, T_DRINK, T_SMOKE, T_AGE, HTN, DM, LIP, WEIGHT, HEIGHT
        with colA:
            EDATE = st.date_input("EDATE(조사일)", value=date.today())  # 필수
            CHILD_sel = st.selectbox("CHILD(임신/출산 경험)", ["선택", 0, 1])  # 필수(0/1)
            SEX_sel   = st.selectbox("SEX(성별)", ["선택", 1, 2])          # 필수(1/2)
            MNSAG = st.number_input("MNSAG(초경나이, 선택)", min_value=-1, step=1, value=-1)  # 선택
            EDU   = st.number_input("EDU(교육수준)", min_value=0, step=1)  # 필수
            SMAG  = st.number_input("SMAG(흡연 시작 나이, 선택)", min_value=-1, step=1, value=-1)  # 선택

        with colB:
            T_DRINK_sel = st.selectbox("T_DRINK(오늘 음주여부)", ["선택", 0, 1])  # 필수
            T_DRINKAM = st.number_input("T_DRINKAM(오늘 음주 주량, 선택)", min_value=-1.0, step=0.1, value=-1.0)  # 선택
            T_SMOKE_sel = st.selectbox("T_SMOKE(오늘 흡연)", ["선택", 0, 1])  # 필수
            T_SMOKEAM = st.number_input("T_SMOKEAM(오늘 흡연량, 선택)", min_value=-1.0, step=0.1, value=-1.0)  # 선택
            T_AGE = st.number_input("T_AGE(나이)", min_value=0, step=1)  # 필수

        with colC:
            HTN_sel = st.selectbox("HTN(기존 고혈압)", ["선택", 0, 1])  # 필수
            DM_sel  = st.selectbox("DM(기존 당뇨병)", ["선택", 0, 1])  # 필수
            LIP_sel = st.selectbox("LIP(기존 고지혈증)", ["선택", 0, 1])  # 필수
            FMMHT = st.number_input("FMMHT(고혈압 엄마, 선택)", min_value=-1, max_value=1, step=1, value=-1)
            FMFHT = st.number_input("FMFHT(고혈압 아빠, 선택)", min_value=-1, max_value=1, step=1, value=-1)
            FMMDM = st.number_input("FMMDM(당뇨병 엄마, 선택)", min_value=-1, max_value=1, step=1, value=-1)
            FMFDM = st.number_input("FMFDM(당뇨병 아빠, 선택)", min_value=-1, max_value=1, step=1, value=-1)

        with colD:
            WEIGHT = st.number_input("WEIGHT(체중 kg)", min_value=0.0, step=0.1)  # 필수 (>0 권장)
            HEIGHT = st.number_input("HEIGHT(신장 cm)", min_value=0.0, step=0.1)  # 필수 (>0 권장)
            WAIST  = st.number_input("WAIST(허리둘레 cm, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            HIP    = st.number_input("HIP(엉덩이둘레 cm, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            SBP    = st.number_input("SBP(수축기 혈압, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            DBP    = st.number_input("DBP(이완기 혈압, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            PULSE  = st.number_input("PULSE(맥박, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            EXER   = st.number_input("EXER(운동 빈도, 선택)", min_value=-1.0, step=0.1, value=-1.0)

        st.markdown("#### 🔬 임상지표(선택 입력 가능)")
        colE, colF = st.columns(2)
        with colE:
            HBA1C = st.number_input("HBA1C(혈당, 선택)", min_value=-1.0, step=0.01, value=-1.0)
            GLU   = st.number_input("GLU(공복혈당, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            HOMAIR= st.number_input("HOMAIR(인슐린 저항성, 선택)", min_value=-1.0, step=0.001, value=-1.0)
            TCHL  = st.number_input("TCHL(총콜레스테롤, 선택)", min_value=-1.0, step=0.1, value=-1.0)
        with colF:
            HDL   = st.number_input("HDL(선택)", min_value=-1.0, step=0.1, value=-1.0)
            TG    = st.number_input("TG(중성지방, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            AST   = st.number_input("AST(간기능, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            ALT   = st.number_input("ALT(간기능, 선택)", min_value=-1.0, step=0.1, value=-1.0)
            CREATININE = st.number_input("CREATININE(신장기능, 선택)", min_value=-1.0, step=0.01, value=-1.0)

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
