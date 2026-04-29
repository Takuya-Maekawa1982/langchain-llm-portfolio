import re
import pytest
from utils.files import extract_raw_content
from utils.files import preprocess_image, segment_lines, postprocess_text
from pathlib import Path
import cv2
import numpy as np


# ============================================
# Helper: テスト用ファイルパス
# ============================================
TEST_DIR = Path(__file__).parent / "samples"

PDF_FILE = TEST_DIR / "sample_invoice.pdf"
IMG_FILE = TEST_DIR / "sample_invoice.jpg"
TXT_FILE = TEST_DIR / "sample.txt"
DOCX_FILE = TEST_DIR / "sample.docx"
XLSX_FILE = TEST_DIR / "sample.xlsx"


# ============================================
# HITL③: LLM に渡す価値チェック関数
# ============================================
def is_valid_for_llm(text: str) -> bool:
    """LLM に渡す価値があるかどうかを判定"""
    if len(text) < 20:
        return False

    if not re.search(r"\d{3,}", text):  # 数字
        return False

    if not re.search(r"\d{4}[-/年]\d{1,2}", text):  # 日付
        return False

    if not ("株式会社" in text or "Inc" in text or "LLC" in text):
        return False

    return True


# ============================================
# 1. ファイル種別判定テスト
# ============================================
def test_file_type_detection():
    print("\n[TEST] ファイル種別判定のテスト")

    with open(PDF_FILE, "rb") as f:
        text, ftype, _ = extract_raw_content(f)
        print("PDF 判定:", ftype)
        assert ftype == "pdf"

    with open(IMG_FILE, "rb") as f:
        text, ftype, _ = extract_raw_content(f)
        print("画像 判定:", ftype)
        assert ftype == "image"

    with open(TXT_FILE, "rb") as f:
        text, ftype, _ = extract_raw_content(f)
        print("TXT 判定:", ftype)
        assert ftype == "text"


# ============================================
# 2. OCR 前処理テスト
# ============================================
def test_preprocess_image():
    print("\n[TEST] OCR 前処理のテスト")

    img = cv2.imread(str(IMG_FILE))
    processed = preprocess_image(img)

    print("前処理後 shape:", processed.shape)
    assert processed is not None
    assert processed.shape[0] > 0
    assert processed.shape[1] > 0


# ============================================
# 3. 行分割テスト
# ============================================
def test_segment_lines():
    print("\n[TEST] 行分割のテスト")

    img = cv2.imread(str(IMG_FILE))
    processed = preprocess_image(img)
    lines = segment_lines(processed)

    print("行数:", len(lines))
    assert len(lines) > 0


# ============================================
# 4. OCR 後処理テスト
# ============================================
def test_postprocess_text():
    print("\n[TEST] OCR 後処理のテスト")

    raw = "O5l 1,200"
    fixed = postprocess_text(raw)

    print("修正前:", raw)
    print("修正後:", fixed)

    assert fixed == "051 1200"


# ============================================
# 5. extract_raw_content の品質テスト
# ============================================
def test_extract_raw_content_quality():
    print("\n[TEST] extract_raw_content の品質テスト")

    with open(PDF_FILE, "rb") as f:
        text, ftype, is_hand = extract_raw_content(f)

    print("抽出テキスト（先頭100文字）:", text[:100])
    print("ファイル種別:", ftype)
    print("手書き判定:", is_hand)

    assert len(text) > 20
    assert re.search(r"\d{3,}", text)  # 数字
    assert re.search(r"\d{4}[-/年]\d{1,2}", text)  # 日付


# ============================================
# 6. HITL③: LLM に渡す価値チェック
# ============================================
def test_value_check():
    print("\n[TEST] HITL③ 価値チェックのテスト")

    valid_text = "株式会社サンプル\nInvoice 2024-03-12\nTotal 5400"
    invalid_text = "aaaaa"

    print("valid_text 判定:", is_valid_for_llm(valid_text))
    print("invalid_text 判定:", is_valid_for_llm(invalid_text))

    assert is_valid_for_llm(valid_text) is True
    assert is_valid_for_llm(invalid_text) is False
