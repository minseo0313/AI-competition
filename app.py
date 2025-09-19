# app.py — 최소 라우터 + 지연 임포트 + 에러 표시
import streamlit as st

st.set_page_config(page_title="만성질환 위험도 예측기", layout="centered")
st.write("✅ app.py loaded")   # 이 줄이 보이면 렌더는 정상

# 세션 라우팅
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_home():
    st.session_state.page = "home"

def go_current():
    st.session_state.page = "current"

def go_future():
    st.session_state.page = "future"

st.caption(f"🧭 current page = {st.session_state.page}")

# ------------------ HOME ------------------
if st.session_state.page == "home":
    st.title("🏠 개인별 생활습관을 이용한 만성질환 위험도 예측기")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("현재 생활습관(단기) 예측"):
            go_current()
    with col2:
        if st.button("지금까지 기록으로 10년 후 예측"):
            go_future()

# ------------------ CURRENT ------------------
elif st.session_state.page == "current":
    st.title("📌 현재 생활습관 기반 만성질환 예측기")
    if st.button("⬅ 홈으로"):
        go_home()
    try:
        import base_health   # 루트에 있는 파일
        base_health.render(go_home)
    except Exception as e:
        st.error("`base_health` 로딩/실행 중 오류가 발생했습니다.")
        st.exception(e)

# ------------------ FUTURE ------------------
elif st.session_state.page == "future":
    st.title("🧬 10년 후 만성질환 시나리오 예측기")
    if st.button("⬅ 홈으로"):
        go_home()
    try:
        import follow_health  # 루트에 있는 파일
        follow_health.render(go_home)
    except Exception as e:
        st.error("`follow_health` 로딩/실행 중 오류가 발생했습니다.")
        st.exception(e)
