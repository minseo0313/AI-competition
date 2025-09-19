"""
utils/preprocess.py
──────────────────────────────────────────────────────────────────────────────
역할:
  - 전처리 단계 모듈화
  - (A) 단기 예측용: 당일 입력 1행 → 파생(BMI/WHR 등) 생성 후 모델 입력 1행
  - (B) 10년 후 예측용: 시계열(여러 시점) → 평균/변화/비율 집계 1행
  - column_meaning 사전(피처 설명) 제공

제공 함수:
  - preprocess_base(row_df: pd.DataFrame) -> pd.DataFrame(1행)
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
# 단기(현재 입력 1행) 전처리
# -------------------------------
def preprocess_base(row_df: pd.DataFrame) -> pd.DataFrame:
    """
    오늘 입력한 단일 행(row_df; 보통 T_ID=1의 마지막 1행)을 받아
    모델 입력용 1행 DataFrame으로 변환합니다.
    - BMI, WHR, TOTAL_DRINK, SMOKE 등 파생을 계산합니다.
    """
    if row_df.empty:
        # 비어 있으면 전부 NaN/-1로 채운 한 행 반환(모델에서 에러 방지)
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
    BMI = (
        r["WEIGHT"] / ((r["HEIGHT"] / 100) ** 2)
        if pd.notna(r["HEIGHT"]) and pd.notna(r["WEIGHT"]) and r["HEIGHT"] > 0
        else np.nan
    )
    WHR = (
        r["WAIST"] / r["HIP"]
        if pd.notna(r["WAIST"]) and pd.notna(r["HIP"]) and r["HIP"] > 0
        else np.nan
    )
    TOTAL_DRINK = r["T_DRINKAM"] if r.get("T_DRINK", 0) == 1 and pd.notna(r["T_DRINKAM"]) else 0
    SMOKE = r["T_SMOKEAM"] if pd.notna(r["T_SMOKEAM"]) else 0

    feat = {
        "T00_ID": str(r.get("T_ID", 1)),
        "T00_SEX": r.get("SEX", -1),
        "T01_CHILD": r.get("CHILD", -1),
        "T01_MNSAG": r.get("MNSAG", -1),
        "T01_EDU": r.get("EDU", -1),
        "T01_SMAG": r.get("SMAG", -1),
        "T01_HTN": r.get("HTN", -1),
        "T01_DM": r.get("DM", -1),
        "T01_LIP": r.get("LIP", -1),

        "T05_FMFHT": r.get("FMFHT", -1),
        "T05_FMMHT": r.get("FMMHT", -1),
        "T05_FMFDM": r.get("FMFDM", -1),
        "T05_FMMDM": r.get("FMMDM", -1),

        "BMI": BMI,
        "WEIGHT": r["WEIGHT"],
        "WHR": WHR,
        "SBP": r["SBP"],
        "DBP": r["DBP"],
        "PULSE": r["PULSE"],
        "TOTAL_DRINK": TOTAL_DRINK,
        "SMOKE": SMOKE,
        "EXER": r["EXER"],
        "HBA1C": r["HBA1C"],
        "GLU": r["GLU"],
        "HOMAIR": r["HOMAIR"],
        "TCHL": r["TCHL"],
        "HDL": r["HDL"],
        "TG": r["TG"],
        "AST": r["AST"],
        "ALT": r["ALT"],
        "CREATININE": r["CREATININE"],

        "T01_AGE": r.get("T_AGE", -1),
    }

    return pd.DataFrame([feat])


# -------------------------------
# 10년 후(시계열 누적) 전처리
# -------------------------------
def preprocess_followup(df_user: pd.DataFrame) -> pd.DataFrame:

    df_user = df_user.sort_values("EDATE").copy()
    df_user = df_user.replace(-1, np.nan)

    features: dict[str, object] = {}
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
    numeric_cols = [
        "HEIGHT", "WEIGHT", "WAIST", "HIP", "SBP", "DBP", "PULSE",
        "T_DRINK", "T_DRINKAM", "T_SMOKE", "T_SMOKEAM",  # ✅ 추가
        "EXER", "HBA1C", "GLU", "HOMAIR",
        "TCHL", "HDL", "TG", "AST", "ALT", "CREATININE"
    ]
    for col in numeric_cols:
        df_user_calc[col] = pd.to_numeric(df_user_calc[col], errors="coerce")

    df_user_calc["BMI"] = df_user_calc.apply(
        lambda r: r["WEIGHT"] / ((r["HEIGHT"] / 100) ** 2)
        if pd.notna(r["HEIGHT"]) and pd.notna(r["WEIGHT"]) and r["HEIGHT"] > 0
        else np.nan,
        axis=1,
    )
    df_user_calc["WHR"] = df_user_calc.apply(
        lambda r: r["WAIST"] / r["HIP"]
        if pd.notna(r["WAIST"]) and pd.notna(r["HIP"]) and r["HIP"] > 0
        else np.nan,
        axis=1,
    )
    df_user_calc["TOTAL_DRINK"] = df_user_calc.apply(
        lambda r: r["T_DRINKAM"]
        if pd.notna(r["T_DRINK"]) and int(r["T_DRINK"]) == 1 and pd.notna(r["T_DRINKAM"])
        else 0,
        axis=1,
    )
    df_user_calc["SMOKE"] = df_user_calc["T_SMOKEAM"].fillna(0)

    def calculate_mean_change(col: str) -> tuple[float, float]:
        vals = df_user_calc[col].dropna().astype(float).tolist()
        if len(vals) == 0:
            return np.nan, np.nan
        mean_val = float(np.mean(vals))
        change_val = vals[-1] - vals[0] if len(vals) > 1 else 0.0
        return mean_val, float(change_val)

    def calculate_ratio(binary_col: str) -> float:
        vals = df_user[binary_col].dropna().tolist()
        return float(sum(vals) / len(vals)) if vals else np.nan

    continuous_cols = [
        "BMI", "WEIGHT", "WHR", "SBP", "DBP", "PULSE", "TOTAL_DRINK", "SMOKE",
        "EXER", "HBA1C", "GLU", "HOMAIR", "TCHL", "HDL", "TG", "AST", "ALT", "CREATININE"
    ]

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
# 공용 컬럼 설명 (팀원 작성 버전 그대로 유지)
# -------------------------------
column_meaning: dict[str, str] = {
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
