"""
utils/preprocess.py
──────────────────────────────────────────────────────────────────────────────
역할:
  - 전처리 단계 모듈화
  - (A) 단기 예측용: 당일 입력 1행 → 파생(BMI/WHR 등) 생성 후 모델 입력 1행
  - (B) 10년 후 예측용: 시계열(여러 시점) → 평균/변화/비율 집계 1행
  - column_meaning 사전(피처 설명) 제공

제공 함수:
  - preprocess_base_dm(row_df: pd.DataFrame) -> pd.DataFrame(1행) - 당뇨병용
  - preprocess_base_htn_lip(row_df: pd.DataFrame) -> pd.DataFrame(1행) - 고혈압/고지혈증용
  - preprocess_base(row_df: pd.DataFrame, disease_type: str) -> pd.DataFrame(1행) - 통합 함수
  - preprocess_followup(df_user: pd.DataFrame) -> pd.DataFrame(1행)
  - column_meaning: Dict[str, str]

주의:
  - 학습 당시 피처 스키마와 반환 컬럼이 일치해야 합니다.
  - 결측/비정상 값은 NaN 처리 후 파생 계산을 합니다.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from collections import Counter


# -------------------------------
# 단기(현재 입력 1행) 전처리 - 질병별 분리
# -------------------------------
def preprocess_base_dm(row_df: pd.DataFrame) -> pd.DataFrame:
    """
    당뇨병 모델용 전처리 (44개 원시 피처)
    """
    if row_df.empty:
        return pd.DataFrame([{}])

    r = row_df.iloc[0].copy()

    # 안전한 수치 변환
    for col in [
        "HEIGHT", "WEIGHT", "WAIST", "HIP", "SBP", "DBP", "PULSE",
        "T_DRINKAM", "T_SMOKEAM", "EXER", "HBA1C", "GLU", "HOMAIR",
        "TCHL", "HDL", "TG", "AST", "ALT", "CREATININE"
    ]:
        r[col] = pd.to_numeric(r.get(col, np.nan), errors="coerce")

    # 파생 계산
    BMI = -1
    if pd.notna(r.get("HEIGHT")) and pd.notna(r.get("WEIGHT")) and r.get("HEIGHT", 0) > 0:
        BMI = r["WEIGHT"] / ((r["HEIGHT"] / 100) ** 2)

    TOTAL_DRINK = r.get("T_DRINKAM", 0) if r.get("T_DRINK") == 3 else 0
    SMOKE = r.get("T_SMOKEAM", 0) if r.get("T_SMOKE") == 3 else 0

    # 당뇨병 모델용 피처 (44개) - 원시 피처
    dm_feat = {
        "T_SEX": r.get("SEX", -1),
        "T_AGE": r.get("T_AGE", -1),
        "T_INCOME": -1,  # 기본값
        "T_MARRY": -1,   # 기본값
        "T_FMFHT1": r.get("FMFHT", -1),
        "T_FMFHT2": r.get("FMMHT", -1),
        "T_FMFDM1": r.get("FMFDM", -1),
        "T_FMFDM2": r.get("FMMDM", -1),
        "T_DRINK": r.get("T_DRINK", -1),
        "T_DRDU": -1,    # 기본값
        "T_TAKFQ": -1,   # 기본값
        "T_TAKAM": -1,   # 기본값
        "T_RICEFQ": -1,  # 기본값
        "T_RICEAM": -1,  # 기본값
        "T_WINEFQ": -1,  # 기본값
        "T_WINEAM": -1,  # 기본값
        "T_SOJUFQ": -1,  # 기본값
        "T_SOJUAM": -1,  # 기본값
        "T_BEERFQ": -1,  # 기본값
        "T_BEERAM": -1,  # 기본값
        "T_HLIQFQ": -1,  # 기본값
        "T_HLIQAM": -1,  # 기본값
        "T_TOTALC": TOTAL_DRINK,
        "T_SMOKE": r.get("T_SMOKE", -1),
        "T_SMDUYR": -1,  # 기본값
        "T_SMDUMO": -1,  # 기본값
        "T_SMAM": SMOKE,
        "T_PACKYR": -1,  # 기본값
        "T_PSM": -1,     # 기본값
        "T_EXER": r.get("EXER", -1),
        "T_MNSAG": r.get("MNSAG", -1),
        "T_PMYN": -1,    # 기본값
        "T_PMAG": -1,    # 기본값
        "T_PREG": -1,    # 기본값
        "T_FPREGAG": -1, # 기본값
        "T_PULSE": r.get("PULSE", -1),
        "T_WAIST": r.get("WAIST", -1),
        "T_HIP": r.get("HIP", -1),
        "T_HEIGHT": r.get("HEIGHT", -1),
        "T_WEIGHT": r.get("WEIGHT", -1),
        "T_BMI": BMI,
        "T_CREATINE": r.get("CREATININE", -1),
        "T_AST": r.get("AST", -1),
        "T_ALT": r.get("ALT", -1),
    }
    
    return pd.DataFrame([dm_feat])


def preprocess_base_htn_lip(row_df: pd.DataFrame) -> pd.DataFrame:
    """
    고혈압/고지혈증 모델용 전처리 (120개 카테고리컬 인코딩된 피처)
    """
    if row_df.empty:
        return pd.DataFrame([{}])

    r = row_df.iloc[0].copy()

    # 안전한 수치 변환
    for col in [
        "HEIGHT", "WEIGHT", "WAIST", "HIP", "SBP", "DBP", "PULSE",
        "T_DRINKAM", "T_SMOKEAM", "EXER", "HBA1C", "GLU", "HOMAIR",
        "TCHL", "HDL", "TG", "AST", "ALT", "CREATININE"
    ]:
        r[col] = pd.to_numeric(r.get(col, np.nan), errors="coerce")

    # 파생 계산
    BMI = -1
    if pd.notna(r.get("HEIGHT")) and pd.notna(r.get("WEIGHT")) and r.get("HEIGHT", 0) > 0:
        BMI = r["WEIGHT"] / ((r["HEIGHT"] / 100) ** 2)

    TOTAL_DRINK = r.get("T_DRINKAM", 0) if r.get("T_DRINK") == 3 else 0
    SMOKE = r.get("T_SMOKEAM", 0) if r.get("T_SMOKE") == 3 else 0

    # 고혈압/고지혈증 모델용 피처 (120개) - 카테고리컬 인코딩된 피처
    feat = {}
    
    # 기본 연속형 피처들
    feat["T_AGE"] = r.get("T_AGE", -1)
    feat["T_TAKAM"] = -1.0
    feat["T_RICEAM"] = -1.0
    feat["T_WINEAM"] = -1.0
    feat["T_SOJUAM"] = -1.0
    feat["T_BEERAM"] = -1.0
    feat["T_HLIQAM"] = -1.0
    feat["T_TOTALC"] = -1.0
    feat["T_SMDUYR"] = -1.0
    feat["T_SMDUMO"] = -1.0
    feat["T_SMAM"] = -1.0
    feat["T_PACKYR"] = -1.0
    feat["T_MNSAG"] = r.get("MNSAG", -1)
    feat["T_PMAG"] = -1.0
    feat["T_FPREGAG"] = -1.0
    feat["T_PULSE"] = r.get("PULSE", -1)
    feat["T_WAIST"] = r.get("WAIST", -1)
    feat["T_HIP"] = r.get("HIP", -1)
    feat["T_HEIGHT"] = r.get("HEIGHT", -1)
    feat["T_WEIGHT"] = r.get("WEIGHT", -1)
    feat["T_BMI"] = BMI
    feat["T_CREATINE"] = r.get("CREATININE", -1)  # 오타: CREATINE
    feat["T_AST"] = r.get("AST", -1)
    feat["T_ALT"] = r.get("ALT", -1)
    
    # 성별 카테고리컬 피처
    sex_val = r.get("SEX", -1)
    feat["T_SEX_1"] = 1 if sex_val == 1 else 0
    feat["T_SEX_2"] = 1 if sex_val == 2 else 0
    
    # 수입 카테고리컬 피처 (기본값: 모두 0)
    for i in range(1, 9):
        feat[f"T_INCOME_{i}.0"] = 0
    
    # 결혼상태 카테고리컬 피처 (기본값: 모두 0)
    for i in range(1, 7):
        feat[f"T_MARRY_{i}.0"] = 0
    
    # 가족력 카테고리컬 피처
    fmmht_val = r.get("FMMHT", -1)
    feat["T_FMFHT1_1"] = 1 if fmmht_val == 1 else 0
    feat["T_FMFHT1_2"] = 1 if fmmht_val == 2 else 0
    
    fmmht_val = r.get("FMMHT", -1)
    feat["T_FMFHT2_1"] = 1 if fmmht_val == 1 else 0
    feat["T_FMFHT2_2"] = 1 if fmmht_val == 2 else 0
    
    fmfdm_val = r.get("FMFDM", -1)
    feat["T_FMFDM1_1"] = 1 if fmfdm_val == 1 else 0
    feat["T_FMFDM1_2"] = 1 if fmfdm_val == 2 else 0
    
    fmfdm_val = r.get("FMFDM", -1)
    feat["T_FMFDM2_1"] = 1 if fmfdm_val == 1 else 0
    feat["T_FMFDM2_2"] = 1 if fmfdm_val == 2 else 0
    
    # 음주 여부 카테고리컬 피처
    drink_val = r.get("T_DRINK", -1)
    feat["T_DRINK_-1.0"] = 1 if drink_val == -1 else 0
    feat["T_DRINK_1.0"] = 1 if drink_val == 1 else 0
    feat["T_DRINK_2.0"] = 1 if drink_val == 2 else 0
    feat["T_DRINK_3.0"] = 1 if drink_val == 3 else 0
    
    # 음주 기간 카테고리컬 피처 (기본값: 모두 0)
    for i in [-1, 1, 2, 3, 4]:
        feat[f"T_DRDU_{i}.0"] = 0
    
    # 모든 음주 빈도 카테고리컬 피처 (기본값: 모두 0)
    drink_types = ["TAK", "RICE", "WINE", "SOJU", "BEER", "HLIQ"]
    for drink_type in drink_types:
        for freq in [-1, 0, 1, 2, 3, 4, 5, 6]:
            feat[f"T_{drink_type}FQ_{freq}.0"] = 0
    
    # 흡연 여부 카테고리컬 피처
    smoke_val = r.get("T_SMOKE", -1)
    feat["T_SMOKE_-1.0"] = 1 if smoke_val == -1 else 0
    feat["T_SMOKE_1.0"] = 1 if smoke_val == 1 else 0
    feat["T_SMOKE_2.0"] = 1 if smoke_val == 2 else 0
    feat["T_SMOKE_3.0"] = 1 if smoke_val == 3 else 0
    
    # 간접 흡연 카테고리컬 피처 (기본값: 모두 0)
    feat["T_PSM_1.0"] = 0
    feat["T_PSM_2.0"] = 0
    
    # 운동 여부 카테고리컬 피처
    exer_val = r.get("EXER", -1)
    feat["T_EXER_-1.0"] = 1 if exer_val == -1 else 0
    feat["T_EXER_1.0"] = 1 if exer_val == 1 else 0
    feat["T_EXER_2.0"] = 1 if exer_val == 2 else 0
    
    # 여성 전용 카테고리컬 피처 (기본값: 모두 0)
    feat["T_PMYN_-1.0"] = 0
    feat["T_PMYN_1.0"] = 0
    feat["T_PMYN_2.0"] = 0
    feat["T_PREG_-1.0"] = 0
    feat["T_PREG_1.0"] = 0
    feat["T_PREG_2.0"] = 0

    return pd.DataFrame([feat])


def preprocess_base(row_df: pd.DataFrame, disease_type: str = "dm") -> pd.DataFrame:
    """
    질병별 전처리 함수 호출
    - disease_type: "dm" (당뇨병), "htn" (고혈압), "lip" (고지혈증)
    """
    if disease_type == "dm":
        return preprocess_base_dm(row_df)
    elif disease_type in ["htn", "lip"]:
        return preprocess_base_htn_lip(row_df)
    else:
        raise ValueError(f"Unknown disease type: {disease_type}")


# -------------------------------
# 10년 후 예측용 전처리
# -------------------------------
def preprocess_followup(df_user: pd.DataFrame) -> pd.DataFrame:
    """
    사용자의 시계열 데이터(df_user; T_ID=1의 여러 행)를 받아
    10년 후 예측용 1행 DataFrame으로 변환합니다.
    - 평균, 변화량, 비율 등을 계산합니다.
    """
    if df_user.empty:
        return pd.DataFrame([{}])

    df_user = df_user.sort_values('EDATE').copy()
    df_user = df_user.replace(-1, np.nan)
    
    features = {}
    features["T00_ID"] = str(df_user["T_ID"].iloc[0])

    vals = df_user["SEX"].dropna().tolist()
    features["T00_SEX"] = Counter(vals).most_common(1)[0][0] if vals else -1

    vals = df_user["CHILD"].dropna().tolist()
    features["T01_CHILD"] = vals[-1] if vals else -1

    for col in ["MNSAG", "EDU", "SMAG"]:
        vals = df_user[col].dropna().tolist()
        features[f"T01_{col}"] = Counter(vals).most_common(1)[0][0] if vals else -1

    for col in ["HTN", "DM", "LIP"]:
        vals = df_user[col].dropna().tolist()
        features[f"T01_{col}"] = vals[-1] if vals else -1

    for col in ["FMFHT", "FMMHT", "FMFDM", "FMMDM"]:
        vals = df_user[col].dropna().tolist()
        features[f"T05_{col}"] = vals[-1] if vals else -1

    df_user_calc = df_user.copy()
    numeric_cols = ["HEIGHT","WEIGHT","WAIST","HIP","SBP","DBP","PULSE",
                    "T_DRINK","T_DRINKAM","T_SMOKE","T_SMOKEAM","EXER","HBA1C","GLU","HOMAIR",
                    "TCHL","HDL","TG","AST","ALT","CREATININE"]
    for col in numeric_cols:
        df_user_calc[col] = pd.to_numeric(df_user_calc[col], errors='coerce')

    df_user_calc["BMI"] = df_user_calc.apply(
        lambda r: r["WEIGHT"]/((r["HEIGHT"]/100)**2) if pd.notna(r["HEIGHT"]) and pd.notna(r["WEIGHT"]) and r["HEIGHT"]>0 else np.nan, axis=1
    )
    df_user_calc["WHR"] = df_user_calc.apply(
        lambda r: r["WAIST"]/r["HIP"] if pd.notna(r["WAIST"]) and pd.notna(r["HIP"]) and r["HIP"]>0 else np.nan, axis=1
    )
    df_user_calc["TOTAL_DRINK"] = df_user_calc.apply(
        lambda r: r["T_DRINKAM"] if pd.notna(r["T_DRINK"]) and r["T_DRINK"]==1 and pd.notna(r["T_DRINKAM"]) else 0, axis=1
    )
    df_user_calc["SMOKE"] = df_user_calc["T_SMOKEAM"].fillna(0)

    def calculate_mean_change(col):
        vals = df_user_calc[col].dropna().astype(float).tolist()
        if len(vals) == 0: return np.nan, np.nan
        mean_val = np.mean(vals)
        change_val = vals[-1]-vals[0] if len(vals)>1 else 0
        return mean_val, change_val

    def calculate_ratio(binary_col):
        vals = df_user[binary_col].dropna().tolist()
        return sum(vals)/len(vals) if vals else np.nan

    continuous_cols = ["BMI","WEIGHT","WHR","SBP","DBP","PULSE","TOTAL_DRINK","SMOKE",
                       "EXER","HBA1C","GLU","HOMAIR","TCHL","HDL","TG","AST","ALT","CREATININE"]

    for col in continuous_cols:
        mean_val, change_val = calculate_mean_change(col)
        features[f"{col}_mean"] = mean_val
        features[f"{col}_change"] = change_val

    features["DRINK_ratio"] = calculate_ratio("T_DRINK")
    features["SMOKE_ratio"] = calculate_ratio("T_SMOKE")

    vals = df_user["T_AGE"].dropna().tolist()
    features["T01_AGE"] = vals[0] if vals else -1

    return pd.DataFrame([features])


# -------------------------------
# 피처 설명 사전
# -------------------------------
column_meaning = {
    "T00_ID": "개인 식별 ID",
    "T01_CHILD": "출산 여부",
    "T00_SEX": "성별",
    "T01_MNSAG": "초경 나이",
    "T01_EDU": "교육수준",
    "T01_SMAG": "흡연 시작 나이",
    "T01_HTN": "기존 고혈압 진단 여부",
    "T01_DM": "기존 당뇨병 진단 여부",
    "T01_LIP": "기존 고지혈증 진단 여부",
    "T05_FMFHT": "고혈압 아빠 질병력 여부",
    "T05_FMMHT": "고혈압 엄마 질병력 여부",
    "T05_FMFDM": "당뇨병 아빠 질병력 여부",
    "T05_FMMDM": "당뇨병 엄마 질병력 여부",
    "BMI_mean": "체질량지수 평균",
    "BMI_change": "체질량지수 변화",
    "WEIGHT_mean": "체중 평균",
    "WEIGHT_change": "체중 변화",
    "WHR_mean": "허리/엉덩이 비율 평균",
    "WHR_change": "허리/엉덩이 비율 변화",
    "SBP_mean": "수축기 혈압 평균",
    "SBP_change": "수축기 혈압 변화",
    "DBP_mean": "이완기 혈압 평균",
    "DBP_change": "이완기 혈압 변화",
    "PULSE_mean": "맥박 평균",
    "PULSE_change": "맥박 변화",
    "TOTAL_DRINK_mean": "총 음주량 평균",
    "TOTAL_DRINK_change": "총 음주량 변화",
    "DRINK_ratio": "전체 기간 중 음주한 시점 비율",
    "SMOKE_mean": "하루 흡연량 평균",
    "SMOKE_change": "하루 흡연량 변화",
    "SMOKE_ratio": "전체 기간 중 흡연한 시점 비율",
    "EXER_mean": "운동 평균",
    "EXER_change": "운동 변화",
    "HBA1C_mean": "혈당 평균",
    "HBA1C_change": "혈당 변화",
    "GLU_mean": "공복혈당 평균",
    "GLU_change": "공복혈당 변화",
    "HOMAIR_mean": "인슐린 저항성 평균",
    "HOMAIR_change": "인슐린 저항성 변화",
    "TCHL_mean": "총콜레스테롤 평균",
    "TCHL_change": "총콜레스테롤 변화",
    "HDL_mean": "HDL 평균",
    "HDL_change": "HDL 변화",
    "TG_mean": "중성지방 평균",
    "TG_change": "중성지방 변화",
    "AST_mean": "간기능(AST) 평균",
    "AST_change": "간기능(AST) 변화",
    "ALT_mean": "간기능(ALT) 평균",
    "ALT_change": "간기능(ALT) 변화",
    "CREATININE_mean": "신장기능 평균",
    "CREATININE_change": "신장기능 변화",
    "T01_AGE": "조사 시작 시점 나이"
}