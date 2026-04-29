import re
import json
from langchain_core.prompts import PromptTemplate
from utils.keys import get_key
from utils.models import ModelFactory
from ..state import BillState

def jp_extractor_node(state: BillState):
    current_retry = state.get("retry_count", 0)
    feedback = state.get("critique", "")

    # --- fallback model list ---
    providers = ModelFactory.get_llm_list(current_retry)

    # --- feedback section ---
    feedback_section = (
        f"\n### PREVIOUS AUDIT FEEDBACK (FIX THIS) ###\n{feedback}"
        if feedback and "RETRY" in feedback.upper()
        else ""
    )

    # --- prompt template (raw string, no indent at start) ---
    template = r"""### ROLE ###
あなたは請求書データ抽出の専門家です。以下の請求書テキストから
必ず **厳密な JSON のみ** を返してください。

### JSON スキーマ（厳密に従うこと） ###
{
    "Invoice ID": "string",
    "Issue Date": "string (YYYY-MM-DD)",
    "DESCRIPTION": "string",
    "UNIT PRICE": "number (float)",
    "AMOUNT": "number (float)",
    "Bill For": "string",
    "From": "string"
}

### 注意事項 ###
- Invoice ID は文字列として扱う（数字・ハイフン・文字をそのまま保持）
- 金額は float に変換（¥, ￥, カンマを除去）
- JSON 以外のテキストを絶対に返さない

### FEW-SHOT EXAMPLES ###

Example 1 (Literal String ID & Numeric Amounts):
Text: 
"請求元：DR-TeleP 〒999-0010 ウェ州ネカスポ市タンネバ通り1583番地 電話：590-327-3987
登録番号: 2,389 | 発行日: 2026/11/27
請求先：ポール・レゲックス 様 〒997-9765 ワ州サターニー市112番通り西1110番地 スイート89626 電話：12876494
項目: 通信基本料 | 単価: ¥500.00 | 金額: ¥500.00"

JSON:
{
    "Invoice ID": "2,389",
    "Issue Date": "2026-11-27",
    "DESCRIPTION": "通信基本料",
    "UNIT PRICE": 500.00,
    "AMOUNT": 500.00,
    "Bill For": "ポール・レゲックス 様 〒997-9765 ワ州サターニー市112番通り西1110番地 スイート89626 電話：12876494",
    "From": "DR-TeleP 〒999-0010 ウェ州ネカスポ市タンネバ通り1583番地 電話：590-327-3987"
}

Example 2 (Alphanumeric ID Preservation):
Text:
"発行元：ギガ通信(株) 〒100-0001 東京都千代田区1-1-1 03-1234-5678
請求番号: 000-852-X | 日付: 2026/04/15
請求先：(株)未来 〒530-0001 大阪府大阪市北区2-2-2 06-9876-5432
摘要: 保守料 | 単価: ￥150,000 | 金額: ￥150,000"

JSON:
{
    "Invoice ID": "000-852-X",
    "Issue Date": "2026-04-15",
    "DESCRIPTION": "保守料",
    "UNIT PRICE": 150000.0,
    "AMOUNT": 150000.0,
    "Bill For": "(株)未来 〒530-0001 大阪府大阪市北区2-2-2 06-9876-5432",
    "From": "ギガ通信(株) 〒100-0001 東京都千代田区1-1-1 03-1234-5678"
}

{feedback_section}

### SOURCE RAW TEXT ###
{pages}

### JSON OUTPUT (STRICTLY JSON ONLY) ###
"""

    prompt_template = PromptTemplate.from_template(template)

    # --- fallback execution ---
    response = None
    active_model = ""

    for p in providers:
        try:
            llm = ModelFactory.create_instance(p)
            if not llm:
                continue

            chain = prompt_template | llm
            response = chain.invoke({
                "pages": state["raw_content"],
                "feedback_section": feedback_section
            })
            active_model = p
            break

        except Exception as e:
            print(f"⚠️ {p} failed: {str(e)[:80]}")
            continue

    if not response:
        return {"extracted_json": {"error": "All providers failed"}}

    # --- JSON extraction ---
    content = response.content.strip()
    content = re.sub(r'```json\s?|```', '', content).strip()

    # 非貪欲マッチで最初の JSON ブロックだけ抽出
    match = re.search(r'\{[\s\S]*?\}', content)
    data_dict = {}

    if match:
        try:
            data_dict = json.loads(match.group(0))
        except:
            data_dict = {"error": "JSON parse failed", "raw": content[:200]}
    else:
        data_dict = {"error": "No JSON found", "raw": content[:200]}

    return {
        "extracted_json": data_dict,
        "audit_logs": [f"JP Step {current_retry}: Extracted by {active_model}"]
    }
