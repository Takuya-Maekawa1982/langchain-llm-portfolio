import re
from ..state import BillState

# 日本語判定（Unicode ブロックベース）
def _detect_language(text: str) -> str:
    # ひらがな・カタカナ・CJK統合漢字
    jp_chars = re.findall(r'[\u3040-\u30FF\u4E00-\u9FFF]', text)
    ratio = len(jp_chars) / max(len(text), 1)

    # 閾値は業務ドメインに応じて調整可能
    # 3% 以上日本語文字があれば日本語とみなす
    return "JP" if ratio > 0.03 else "EN"


def lang_detector_node(state: BillState):
    raw = state.get("raw_content", "") or ""
    sample = raw[:2500]

    # LLM を使わずにローカル判定
    language = _detect_language(sample)

    # 手書き判定はここでは行わない（常に False）
    # → 必要なら OCR ノード側で画像ベースに実装する想定
    is_handwritten = False

    # 監査ログ（どのロジックを使ったかだけ残す）
    model_log = "Step 0 (Inspect): Local heuristic (no LLM)"

    return {
        "language": language,
        "is_handwritten": is_handwritten,
        "retry_count": 0,
        "status": "inspected",
        "audit_logs": [model_log],
    }
