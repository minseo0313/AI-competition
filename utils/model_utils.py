"""
모델 관련 유틸 함수 모음
- 모델 로딩 (joblib)
- 공통 예측 함수
"""

import joblib
import streamlit as st
import os

MODEL_DIR = "models"

@st.cache_resource
def load_models(kind="follow"):
    """
    모델 로딩 함수
    kind = "follow" (10년 후 예측)
         = "base" (단기 예측)
    """
    if kind == "follow":
        model_htn = joblib.load(os.path.join(MODEL_DIR, "follow_model_htn.joblib"))
        model_dm = joblib.load(os.path.join(MODEL_DIR, "follow_model_dm.joblib"))
        model_lip = joblib.load(os.path.join(MODEL_DIR, "follow_model_lip.joblib"))
    else:
        model_htn = joblib.load(os.path.join(MODEL_DIR, "base_model_htn.joblib"))
        model_dm = joblib.load(os.path.join(MODEL_DIR, "base_model_dm.joblib"))
        model_lip = joblib.load(os.path.join(MODEL_DIR, "base_model_lip.joblib"))

    return {
        "고혈압": model_htn,
        "당뇨병": model_dm,
        "고지혈증": model_lip
    }

