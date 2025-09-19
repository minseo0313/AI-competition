# -------------------------------
# GPT로 자연어 설명 생성 (최신 SDK)
# -------------------------------

import streamlit as st
import openai


openai.api_key = st.secrets["OPENAI_API_KEY"]


def generate_gpt_explanation(user_data, column_meaning, results_prob, feature_importances):
    prompt = f"""
사용자 데이터: {user_data}
각 컬럼별 의미: {column_meaning}
모델 예측 확률: {results_prob}
각 질병별 예측에 가장 큰 영향을 준 컬럼: {feature_importances}

위 정보를 기반으로, 다섯줄 이내로 사용자가 이해할 수 있는 자연어 설명을 만들어줘.
- 위험 요인(생활 습관, 신체 지표) 포함
- 건강 관리 권장사항 포함
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 건강 정보를 쉽게 설명하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    explanation = response.choices[0].message.content
    return explanation
