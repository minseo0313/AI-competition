"""
utils/io_utils.py
──────────────────────────────────────────────
역할:
- 데이터/모델 경로 상수 정의
- CSV 존재 보장, 로드, 행 추가(append) 유틸
- follow_sample.csv 입출력 단일 진입점
"""

import os
import pandas as pd
from datetime import datetime

# -------------------------------
# 경로 상수
# -------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
MODEL_DIR = os.path.join(ROOT, "models")

CSV_PATH = os.path.join(DATA_DIR, "follow_sample.csv")

# follow_sample.csv 의 표준 스키마 (컬럼 순서 통일용)
COLUMNS = [
    "T_ID", "EDATE",
    "CHILD", "SEX", "MNSAG", "EDU", "SMAG",
    "T_DRINK", "T_DRINKAM", "T_SMOKE", "T_SMOKEAM", "T_AGE",
    "HTN", "DM", "LIP",
    "FMMHT", "FMFHT", "FMMDM", "FMFDM",
    "WEIGHT", "HEIGHT", "WAIST", "HIP", "SBP", "DBP", "PULSE", "EXER",
    "HBA1C", "GLU", "HOMAIR",
    "TCHL", "HDL", "TG", "AST", "ALT", "CREATININE"
]

# -------------------------------
# CSV 파일 보장
# -------------------------------
def ensure_csv():
    """CSV 파일이 없으면 헤더만 있는 파일 생성"""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


# -------------------------------
# CSV/XLSX 로드
# -------------------------------
def load_df() -> pd.DataFrame:
    """
    CSV를 DataFrame으로 로드
    - 없으면 XLSX 불러와 CSV 생성
    """
    ensure_csv()
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    else:
        return pd.DataFrame(columns=COLUMNS)


# -------------------------------
# 행 추가 (append)
# -------------------------------
def append_row(row: dict):
    """
    한 행(dict)을 follow_sample.csv 에 누적 저장
    - 공란(None/"")은 -1로 통일
    - EDATE는 YYYY-MM-DD 문자열로 저장 (이미 CSV도 같은 포맷임)
    """
    ensure_csv()

    clean = {}
    for col in COLUMNS:
        val = row.get(col, -1)

        if val is None or (isinstance(val, str) and val.strip() == ""):
            val = -1

        if col == "EDATE" and val != -1:
            # datetime 객체만 처리 → 나머지는 그대로 둠 (YYYY-MM-DD)
            if not isinstance(val, str):
                val = pd.to_datetime(val).strftime("%Y-%m-%d")

        clean[col] = val

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df = pd.concat([df, pd.DataFrame([clean])], ignore_index=True)

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
