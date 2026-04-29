from utils.models import ModelFactory
from ..state import BillState

def summarizer_node(state: BillState):
    # 履歴リストを取得（安全のため get を使用）
    logs = state.get("audit_logs", [])
    
    # 1. ログが少ない、またはAudit Modeがオフの場合は簡潔に
    if not logs or len(logs) <= 1:
        summary = "Standard extraction completed successfully."
        return {"audit_summary": summary}

    # 2. 通信失敗に備えたフォールバック付き実行
    try:
        # 要約には最速・最安の Gemini-Lite を使用
        llm = ModelFactory.create_instance("Gemini-Lite")
        
        history = "\n".join(logs)
        prompt = f"""
        Based on these invoice processing logs, provide a one-sentence summary for the user.
        Highlight which issues were resolved (e.g., 'Switched to Gemini to fix a missing address').
        
        LOGS:
        {history}
        
        SUMMARY:
        """
        
        response = llm.invoke(prompt)
        summary = response.content.strip()
    except Exception as e:
        # LLM要約自体が失敗しても、グラフを止めないためのガード
        summary = f"Processed with {len(logs)} steps (Summary generation failed)."

    return {"audit_summary": summary}