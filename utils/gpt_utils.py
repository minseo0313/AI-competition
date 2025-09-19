# -------------------------------
# GPT로 자연어 설명 생성 (최신 SDK)
# -------------------------------

import streamlit as st
import openai


# API 키 설정 (secrets.toml 또는 환경변수에서)
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except:
    # secrets.toml이 없거나 키가 없는 경우 환경변수에서 시도
    import os
    openai.api_key = os.getenv("OPENAI_API_KEY", "개인 키")  # 실제 키로 바꾸기


def generate_gpt_explanation(user_data, column_meaning, results_prob, feature_importances):
    try:
        # 한국어 문자열을 안전하게 처리
        import json
        
        # 딕셔너리를 JSON 문자열로 변환 (한국어 지원)
        user_data_str = json.dumps(user_data, ensure_ascii=False, indent=2)
        column_meaning_str = json.dumps(column_meaning, ensure_ascii=False, indent=2)
        results_prob_str = json.dumps(results_prob, ensure_ascii=False, indent=2)
        feature_importances_str = json.dumps(feature_importances, ensure_ascii=False, indent=2)
        
        prompt = f"""
사용자 데이터: {user_data_str}
각 컬럼별 의미: {column_meaning_str}
모델 예측 확률: {results_prob_str}
각 질병별 예측에 가장 큰 영향을 준 컬럼: {feature_importances_str}

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
        
    except Exception as e:
        # GPT 호출 실패 시 기본 설명 반환
        return f"""
예측 결과 요약:
- 고혈압: {results_prob.get('고혈압', 0):.1%}
- 당뇨병: {results_prob.get('당뇨병', 0):.1%}  
- 고지혈증: {results_prob.get('고지혈증', 0):.1%}

위험도가 높은 질병에 대해서는 정기적인 건강 검진과 생활습관 개선을 권장합니다.
(GPT 설명 생성 중 오류가 발생했습니다: {str(e)})
"""
