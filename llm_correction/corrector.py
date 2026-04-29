import re
from langchain_core.prompts import PromptTemplate
from utils.text_llm_router import TextLLMRouter


def llm_correction(text: str, lang: str, retry_count: int = 0):
    """
    LangGraph の外で使う LLM Correction（任意）
    - Router + Factory の最新構造に完全準拠
    """

    # 言語分岐
    if lang == "JP":
        role = "あなたはOCR誤読の修正専門家です。誤読のみ修正し、内容を追加・削除・要約しないでください。"
    else:
        role = "You are an OCR correction specialist. Fix ONLY OCR mistakes. Do NOT summarize, add, or remove content."

    template = f"""
    ### ROLE ###
    {role}

    ### RAW OCR TEXT ###
    {{raw_text}}

    ### OUTPUT ###
    Return ONLY the corrected text.
    """

    prompt = PromptTemplate.from_template(template).format(raw_text=text)

    logs = []

    # ★ Router でモデルを選ぶ（最新構造）
    router_result = TextLLMRouter.get_callable(retry_count)

    if not router_result["ok"]:
        logs.extend(router_result["errors"])
        logs.append("LLM correction failed on all providers")
        return {
            "corrected_text": text,
            "model": None,
            "success": False,
            "logs": logs,
        }

    model_callable = router_result["callable"]
    model_info = router_result["model"]
    logs.append(f"Router selected model: {model_info}")

    # ★ 実行
    try:
        response = model_callable(prompt)
        if response is None:
            logs.append("Model returned None")
            return {
                "corrected_text": text,
                "model": model_info,
                "success": False,
                "logs": logs,
            }

    except Exception as e:
        logs.append(f"Model execution failed: {str(e)[:80]}")
        return {
            "corrected_text": text,
            "model": model_info,
            "success": False,
            "logs": logs,
        }

    # 出力クリーンアップ
    content = response.strip()
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL).strip()

    logs.append(f"LLM correction succeeded with {model_info}")

    return {
        "corrected_text": content,
        "model": model_info,
        "success": True,
        "logs": logs,
    }
