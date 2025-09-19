# app.py — 최소 라우터 + 지연 임포트 + 에러 표시
import streamlit as st

st.set_page_config(page_title="만성질환 위험도 예측기", layout="centered")

# 세션 라우팅
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_home():
    st.session_state.page = "home"

def go_current():
    st.session_state.page = "current"

def go_future():
    st.session_state.page = "future"

# ------------------ HOME ------------------
if st.session_state.page == "home":
    st.title("🏠 개인별 생활습관을 이용한 만성질환 위험도 예측기")
    st.write("아래 버튼을 눌러 원하는 예측기를 선택하세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("현재 내 생활습관을 기반으로 만성질환 위험도 예측하기"):
            go_current()
    with col2:
        if st.button("지금까지의 내 생활습관을 기반으로 10년 후 만성질환 위험도 예측하기"):
            go_future()

# ------------------ CURRENT ------------------
elif st.session_state.page == "current":
    try:
        import base_health   # 루트에 있는 파일
        base_health.render(go_home)
    except Exception as e:
        st.error("`base_health` 로딩/실행 중 오류가 발생했습니다.")
        st.exception(e)

# ------------------ FUTURE ------------------
elif st.session_state.page == "future":
    try:
        import follow_health  # 루트에 있는 파일
        follow_health.render(go_home)
    except Exception as e:
        st.error("`follow_health` 로딩/실행 중 오류가 발생했습니다.")
        st.exception(e)
