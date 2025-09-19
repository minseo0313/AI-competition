# follow_health.py
"""
10년 후 만성질환 시나리오 예측 페이지 (루트 배치용)

- data/follow_sample.csv 로드 → T_ID=1 사용자 누적 데이터 필터
- utils.preprocess.preprocess_followup() 으로 시계열 요약 전처리
- utils.model_utils.load_models(kind="follow") 로 모델 3종 로드
- 예측/확률/중요도 출력 + GPT 자연어 설명
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.preprocess import preprocess_followup, column_meaning
from utils.model_utils import load_models
from utils.gpt_utils import generate_gpt_explanation


def render(go_home):
    st.title("🧬 10년 후 만성질환 시나리오 예측기")
    st.write("지금까지 기록해주신 생활습관을 바탕으로 10년 후 만성질환 위험도를 예측합니다.")

    if st.button("⬅ 홈으로 돌아가기"):
        go_home()

    st.divider()

    if st.button("예측하기"):
        try:
            with st.spinner("예측을 준비하는 중..."):
                # 1) 데이터 로드
                df = pd.read_csv("data/follow_sample.csv", encoding="utf-8-sig")

                # 날짜/ID 안전 캐스팅
                if "EDATE" in df.columns:
                    df["EDATE"] = pd.to_datetime(df["EDATE"], errors="coerce")
                if "T_ID" in df.columns:
                    df["T_ID"] = pd.to_numeric(df["T_ID"], errors="coerce")

                # 2) 특정 사용자(T_ID=1) 필터
                df_user = df[df["T_ID"] == 1]
                if df_user.empty:
                    st.error("T_ID=1 사용자 데이터를 찾을 수 없습니다. (먼저 ‘현재 입력’ 페이지에서 데이터를 저장하세요)")
                    return

                # 3) 전처리 (시계열 요약)
                input_df = preprocess_followup(df_user)

                # 4) 모델 로딩(10년 후 예측용)
                try:
                    models = load_models(kind="follow")
                except FileNotFoundError:
                    st.info("10년 후 예측용 모델(`follow_model_*.joblib`)이 없습니다.\n"
                            "모델 파일을 `models/` 폴더에 넣고 다시 시도하세요.")
                    return

                # 5) 예측/확률/중요도 출력
                results_prob: dict[str, float] = {}
                feature_importances: dict[str, list[tuple[str, float]]] = {}

                st.subheader("📊 예측 결과")
                for disease_name, model in models.items():
                    pred = model.predict(input_df)[0]
                    prob = float(model.predict_proba(input_df)[0][1])
                    results_prob[disease_name] = prob

                    if hasattr(model, "feature_importances_"):
                        importances = model.feature_importances_
                        feat_names = input_df.columns
                        top_idx = np.argsort(importances)[::-1][:3]
                        top_feats = [(feat_names[i], float(importances[i])) for i in top_idx]
                        feature_importances[disease_name] = top_feats
                    else:
                        feature_importances[disease_name] = []

                    st.write(
                        f"**{disease_name}**: {'발생 가능성 높음' if pred==1 else '발생 가능성 낮음'} "
                        f"(확률: {prob:.2%})"
                    )

                # 요약 테이블
                st.dataframe(
                    pd.DataFrame({
                        "질병": list(results_prob.keys()),
                        "발생확률": [f"{p:.1%}" for p in results_prob.values()]
                    }),
                    use_container_width=True
                )

                # 중요도 표(있을 때만)
                for disease, feats in feature_importances.items():
                    if feats:
                        st.markdown(f"**{disease} 영향 상위 피처**")
                        st.table(pd.DataFrame(feats, columns=["피처", "중요도"]))

                # 6) GPT 설명
                user_data = input_df.to_dict(orient="records")[0]
                explanation = generate_gpt_explanation(
                    user_data=user_data,
                    column_meaning=column_meaning,
                    results_prob=results_prob,
                    feature_importances=feature_importances,
                )

            st.subheader("📝 AI가 설명해주는 예측 결과")
            st.write(explanation)

        except FileNotFoundError:
            st.error("데이터 파일을 찾을 수 없습니다. `data/follow_sample.csv` 경로를 확인하세요.")
        except Exception as e:
            st.error(f"에러 발생: {e}")
