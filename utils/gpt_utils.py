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
    # GPT API 호출을 임시로 비활성화하고 기본 설명 반환
    # 인코딩 문제 해결을 위해
    try:
        # 기본 설명 생성 (인코딩 문제 없이)
        explanation_parts = []
        
        # 위험도가 높은 질병 찾기
        high_risk_diseases = []
        for disease, prob in results_prob.items():
            if prob > 0.3:  # 30% 이상이면 위험도 높음
                high_risk_diseases.append(f"{disease}({prob:.1%})")
        
        explanation_parts.append("📊 예측 결과 요약:")
        explanation_parts.append(f"- 고혈압: {results_prob.get('고혈압', 0):.1%}")
        explanation_parts.append(f"- 당뇨병: {results_prob.get('당뇨병', 0):.1%}")
        explanation_parts.append(f"- 고지혈증: {results_prob.get('고지혈증', 0):.1%}")
        explanation_parts.append("")
        
        if high_risk_diseases:
            explanation_parts.append(f"⚠️ 주의가 필요한 질병: {', '.join(high_risk_diseases)}")
            explanation_parts.append("정기적인 건강 검진과 생활습관 개선을 권장합니다.")
        else:
            explanation_parts.append("✅ 현재 예측 결과로는 모든 질병의 위험도가 낮습니다.")
            explanation_parts.append("현재 생활습관을 유지하시기 바랍니다.")
        
        explanation_parts.append("")
        explanation_parts.append("💡 건강 관리 팁:")
        explanation_parts.append("- 규칙적인 운동과 균형 잡힌 식단 유지")
        explanation_parts.append("- 금연, 금주 및 스트레스 관리")
        explanation_parts.append("- 정기적인 건강 검진 받기")
        
        return "\n".join(explanation_parts)
        
    except Exception as e:
        # 최종 안전장치 - 간단한 설명만 반환
        try:
            return f"""예측 결과 요약:
- 고혈압: {results_prob.get('고혈압', 0):.1%}
- 당뇨병: {results_prob.get('당뇨병', 0):.1%}  
- 고지혈증: {results_prob.get('고지혈증', 0):.1%}

위험도가 높은 질병에 대해서는 정기적인 건강 검진과 생활습관 개선을 권장합니다."""
        except:
            return "예측 결과를 불러오는 중 문제가 발생했습니다. 다시 시도해주세요."
