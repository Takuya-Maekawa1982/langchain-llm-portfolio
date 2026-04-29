import json
import re
from utils.models import ModelFactory
from ..state import BillState

def inspector_node(state: BillState):
    # ModelFactory の公式リストを使用
    providers = ModelFactory.get_llm_list(state.get("retry_count", 0))
    
    # 判定精度を上げるための指示
    prompt = f"""
    Analyze the following billing document text.
    1. Language: Identify if the text is primarily 'JP' (Japanese) or 'EN' (English).
    2. Handwritten: Check for any signatures or handwritten marks (true/false).

    TEXT SAMPLE:
    {state['raw_content'][:2500]}

    RETURN ONLY JSON:
    {{"language": "JP", "is_handwritten": false}}
    """
    
    response = None
    active_model = ""

    # 実行ループ
    for p in providers:
        llm = ModelFactory.create_instance(p)
        if not llm: 
            continue 
        
        try:
            response = llm.invoke(prompt)
            active_model = p
            break
        except Exception as e:
            # ログを具体的に残す
            print(f"⚠️ Inspector Error: {p} -> {str(e)[:1000]}")
            continue

    # デフォルト値の安全策
    # (全失敗時に "JP" を含む文字列があれば JP に倒すロジックを保険で追加)
    default_lang = "JP" if any(c in state['raw_content'] for c in "あいうえおかきくけこ") else "EN"
    res_data = {"language": default_lang, "is_handwritten": False}
    
    if response:
        try:
            # Markdownの除去とJSON抽出
            content = re.sub(r'```json\s?|```', '', response.content).strip()
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match:
                res_data = json.loads(match.group(1))
        except Exception:
            pass

    # 監査用ログの生成
    model_log = f"Step 0 (Inspect): Used {active_model}" if active_model else "Step 0 (Inspect): All API Failed"
    
    return {
        "language": res_data.get("language", default_lang),
        "is_handwritten": res_data.get("is_handwritten", False),
        "retry_count": 0,
        "status": "inspected",
        "audit_logs": [model_log] # critiqueではなくaudit_logsに一貫して保存
    }