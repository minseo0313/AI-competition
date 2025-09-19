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
            CHILD_sel = st.selectbox("🤱 출산 여부 (CHILD)", ["선택", "낳지 않았다 (1)", "낳았다 (2)"])
            SEX_sel = st.selectbox("👤 성별 (SEX)", ["선택", "남자 (1)", "여자 (2)"])
            EDU_sel = st.selectbox("🎓 교육수준 (EDU)", ["선택", "초등학교 이하 (1)", "중학교 (2)", "고등학교 (3)", "전문대 (4)", "대학교 (5)", "대학원 이상 (6)"])
            T_AGE = st.number_input("🎂 나이 (T_AGE)", min_value=0, step=5, format="%d")
        
        with colB:
            st.markdown("**생활습관 & 기존 질환**")
            T_DRINK_sel = st.selectbox("🍺 음주 여부 (T_DRINK)", ["선택", "비음주 (1)", "과거음주 (2)", "현재음주 (3)"])
            T_SMOKE_sel = st.selectbox("🚬 흡연 여부 (T_SMOKE)", ["선택", "비흡연 (1)", "과거흡연 (2)", "현재흡연 (3)"])
            HTN_sel = st.selectbox("🩺 기존 고혈압 (HTN)", ["선택", "없음 (1)", "있음 (2)"])
            DM_sel = st.selectbox("🍯 기존 당뇨병 (DM)", ["선택", "없음 (1)", "있음 (2)"])
            LIP_sel = st.selectbox("🩸 기존 고지혈증 (LIP)", ["선택", "없음 (1)", "있음 (2)"])
        
        st.markdown("**신체지표**")
        colC, colD = st.columns(2)
        with colC:
            WEIGHT = st.number_input("⚖️ 체중 (WEIGHT) - kg", min_value=0.0, step=1.0, format="%.1f")
        with colD:
            HEIGHT = st.number_input("📏 신장 (HEIGHT) - cm", min_value=0.0, step=5.0, format="%.1f")
        
        st.divider()
        
        # 선택 항목 섹션
        st.markdown("### 🟡 선택 입력 항목")
        st.info("아래 항목들은 선택사항입니다. 모르는 경우 입력하지 않으셔도 됩니다.")
        
        colE, colF, colG = st.columns(3)
        
        with colE:
            st.markdown("**추가 개인정보**")
            MNSAG = st.number_input("🌙 초경나이 (MNSAG)", min_value=-1, step=2, value=-1, format="%d")
            SMAG = st.number_input("🚬 흡연 시작 나이 (SMAG)", min_value=-1, step=5, value=-1, format="%d")
            
        with colF:
            st.markdown("**가족력**")
            FMMHT_sel = st.selectbox("👩 고혈압 엄마 (FMMHT)", ["모름", "없음 (1)", "있음 (2)"])
            FMFHT_sel = st.selectbox("👨 고혈압 아빠 (FMFHT)", ["모름", "없음 (1)", "있음 (2)"])
            FMMDM_sel = st.selectbox("👩 당뇨병 엄마 (FMMDM)", ["모름", "없음 (1)", "있음 (2)"])
            FMFDM_sel = st.selectbox("👨 당뇨병 아빠 (FMFDM)", ["모름", "없음 (1)", "있음 (2)"])
        
        with colG:
            st.markdown("**음주/흡연 상세**")
            T_DRINKAM = st.number_input("🍺 오늘 음주량 (T_DRINKAM)", min_value=-1.0, step=1.0, value=-1.0, format="%.1f")
            T_SMOKEAM = st.number_input("🚬 오늘 흡연량 (T_SMOKEAM)", min_value=-1.0, step=1.0, value=-1.0, format="%.1f")
        
        st.markdown("**신체 측정값**")
        colH, colI = st.columns(2)
        with colH:
            WAIST = st.number_input("📐 허리둘레 (WAIST) - cm", min_value=-1.0, step=5.0, value=-1.0, format="%.1f")
            HIP = st.number_input("📐 엉덩이둘레 (HIP) - cm", min_value=-1.0, step=5.0, value=-1.0, format="%.1f")
            SBP = st.number_input("💓 수축기 혈압 (SBP) - mmHg", min_value=-1.0, step=10.0, value=-1.0, format="%.1f")
            DBP = st.number_input("💓 이완기 혈압 (DBP) - mmHg", min_value=-1.0, step=5.0, value=-1.0, format="%.1f")
        with colI:
            PULSE = st.number_input("💗 맥박 (PULSE) - bpm", min_value=-1.0, step=10.0, value=-1.0, format="%.1f")
            EXER = st.number_input("🏃 운동 빈도 (EXER)", min_value=-1.0, step=1.0, value=-1.0, format="%.1f")

        st.markdown("**🔬 임상지표 (검사 결과)**")
        colJ, colK = st.columns(2)
        with colJ:
            HBA1C = st.number_input("🩸 당화혈색소 (HBA1C) - %", min_value=-1.0, step=0.5, value=-1.0, format="%.2f")
            GLU = st.number_input("🍯 공복혈당 (GLU) - mg/dL", min_value=-1.0, step=10.0, value=-1.0, format="%.1f")
            HOMAIR = st.number_input("⚡ 인슐린저항성 (HOMAIR)", min_value=-1.0, step=0.5, value=-1.0, format="%.3f")
            TCHL = st.number_input("🩸 총콜레스테롤 (TCHL) - mg/dL", min_value=-1.0, step=10.0, value=-1.0, format="%.1f")
        with colK:
            HDL = st.number_input("🩸 HDL콜레스테롤 (HDL) - mg/dL", min_value=-1.0, step=5.0, value=-1.0, format="%.1f")
            TG = st.number_input("🩸 중성지방 (TG) - mg/dL", min_value=-1.0, step=10.0, value=-1.0, format="%.1f")
            AST = st.number_input("🩸 AST (간기능) - U/L", min_value=-1.0, step=5.0, value=-1.0, format="%.1f")
            ALT = st.number_input("🩸 ALT (간기능) - U/L", min_value=-1.0, step=5.0, value=-1.0, format="%.1f")
            CREATININE = st.number_input("🩸 크레아티닌 (신장기능) - mg/dL", min_value=-1.0, step=0.1, value=-1.0, format="%.2f")

            # 질병 선택
            st.markdown("**🎯 예측할 질병 선택**")
            disease_choice = st.selectbox(
                "예측하고 싶은 질병을 선택하세요:",
                ["당뇨병", "고혈압", "고지혈증"],
                help="각 질병별로 다른 모델을 사용합니다."
            )

            submitted = st.form_submit_button("💾 저장하고 단기 예측 실행")

    # -------------------------------
    # 저장 + 검증 + 단기 예측
    # -------------------------------
    if submitted:
        # 1) 필수값 검증 및 숫자 변환
        errors = []
        
        # 선택지에서 숫자로 변환하는 함수
        def parse_selection(selection, choices):
            if selection == "선택":
                return None
            for choice in choices:
                if selection == choice:
                    return choices[choice]
            return None
        
        # 기본 정보 파싱
        CHILD = None if CHILD_sel == "선택" else (1 if "낳지 않았다" in CHILD_sel else 2)
        SEX = None if SEX_sel == "선택" else (1 if "남자" in SEX_sel else 2)
        EDU = None if EDU_sel == "선택" else int(EDU_sel.split("(")[1].split(")")[0])
        
        # 음주/흡연 파싱
        T_DRINK = None if T_DRINK_sel == "선택" else int(T_DRINK_sel.split("(")[1].split(")")[0])
        T_SMOKE = None if T_SMOKE_sel == "선택" else int(T_SMOKE_sel.split("(")[1].split(")")[0])
        
        # 질병 진단 파싱
        HTN = None if HTN_sel == "선택" else int(HTN_sel.split("(")[1].split(")")[0])
        DM = None if DM_sel == "선택" else int(DM_sel.split("(")[1].split(")")[0])
        LIP = None if LIP_sel == "선택" else int(LIP_sel.split("(")[1].split(")")[0])
        
        # 가족력 파싱
        FMMHT = -1 if FMMHT_sel == "모름" else int(FMMHT_sel.split("(")[1].split(")")[0])
        FMFHT = -1 if FMFHT_sel == "모름" else int(FMFHT_sel.split("(")[1].split(")")[0])
        FMMDM = -1 if FMMDM_sel == "모름" else int(FMMDM_sel.split("(")[1].split(")")[0])
        FMFDM = -1 if FMFDM_sel == "모름" else int(FMFDM_sel.split("(")[1].split(")")[0])

        # 필수 항목 검증
        if EDATE is None:
            errors.append("조사일을 선택하세요.")
        if CHILD is None:
            errors.append("출산 여부를 선택하세요.")
        if SEX is None:
            errors.append("성별을 선택하세요.")
        if EDU is None:
            errors.append("교육수준을 선택하세요.")
        if T_DRINK is None:
            errors.append("음주 여부를 선택하세요.")
        if T_SMOKE is None:
            errors.append("흡연 여부를 선택하세요.")
        if T_AGE is None or T_AGE < 0:
            errors.append("나이를 올바르게 입력하세요.")
        if HTN is None:
            errors.append("고혈압 진단 여부를 선택하세요.")
        if DM is None:
            errors.append("당뇨병 진단 여부를 선택하세요.")
        if LIP is None:
            errors.append("고지혈증 진단 여부를 선택하세요.")
        if WEIGHT is None or WEIGHT <= 0:
            errors.append("체중을 0보다 크게 입력하세요.")
        if HEIGHT is None or HEIGHT <= 0:
            errors.append("신장을 0보다 크게 입력하세요.")

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
            
            # 질병별 전처리 및 모델 로드
            disease_map = {"당뇨병": "dm", "고혈압": "htn", "고지혈증": "lip"}
            disease_code = disease_map[disease_choice]
            X = preprocess_base(last_row_df, disease_code)

            # 해당 질병 모델만 로드
            model_path = f"models/base_model_{disease_code}.joblib"
            try:
                import joblib
                model = joblib.load(model_path)
                
                with st.spinner(f"{disease_choice} 예측 실행 중..."):
                    st.subheader(f"⚡ {disease_choice} 예측 결과")
                    prob = float(model.predict_proba(X)[0][1])
                    pred = int(model.predict(X)[0])
                    
                    st.metric(
                        label=f"{disease_choice} 발생 위험도",
                        value=f"{prob:.1%}",
                        delta="높음" if pred == 1 else "낮음"
                    )
                    
                    if prob > 0.7:
                        st.warning("⚠️ 위험도가 높습니다. 정기적인 건강 검진을 권장합니다.")
                    elif prob > 0.4:
                        st.info("ℹ️ 주의가 필요합니다. 생활습관 개선을 권장합니다.")
                    else:
                        st.success("✅ 위험도가 낮습니다. 현재 생활습관을 유지하세요.")
                        
            except FileNotFoundError:
                st.error(f"❌ {disease_choice} 모델 파일을 찾을 수 없습니다: {model_path}")
            except Exception as e:
                st.error(f"❌ {disease_choice} 예측 중 오류 발생: {e}")

            # 6) 최근 입력 미리보기
            with st.expander("📄 최근 입력(상위 5행) 보기"):
                st.dataframe(df_user.tail(5), use_container_width=True)

        except FileNotFoundError:
            st.error("데이터 파일을 찾을 수 없습니다. data/follow_sample.csv 경로를 확인하세요.")
        except Exception as e:
            st.error(f"에러 발생: {e}")
