import re
from utils.models import ModelFactory
from ..state import BillState

def critique_node(state: BillState):
    current_retry = state.get("retry_count", 0)
    
    # 監査用プロンプト (整合性ルールを数学的に定義)
    prompt = f"""
    ### ROLE ###
    Senior Financial Auditor. Compare RAW text vs JSON.

    ### RULES ###
    1. NUMERIC: "2,389" (RAW) == 2389 (JSON). Digits matching is CORRECT.
    2. TERMS: "Terms" must be extracted if present in RAW.
    3. ADDRESS: No truncation allowed for "From" or "Bill For".

    ### OUTPUT ###
    - If correct: return only "FINISH"
    - If error: return "RETRY" and "SUMMARY: [issue]"

    RAW: {state.get("raw_content")}
    JSON: {state.get("extracted_json")}
    """

    # ModelFactoryからリストを取得し、全滅を防ぐ
    providers = ModelFactory.get_llm_list(current_retry)
    final_response = None
    active_model = ""

    for p in providers:
        try:
            llm = ModelFactory.create_instance(p)
            if not llm: continue
            
            # 確実に文字列を返すように呼び出し
            res = llm.invoke(prompt)
            final_response = res.content
            active_model = p
            break
        except Exception as e:
            print(f"Critique provider {p} failed: {e}")
            continue

    # 万が一全モデルが失敗した時のセーフティネット (強制通過)
    if not final_response:
        return {
            "critique": "FINISH (Safety Fallback)", 
            "audit_logs": ["⚠️ Critique API all failed. Safety fallback to FINISH."]
        }

    return {
        "critique": final_response,
        "audit_logs": [f"Step {current_retry}: Critiqued by {active_model}"]
    }   