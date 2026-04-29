import re
from langchain_core.prompts import PromptTemplate
from utils.models import ModelFactory
from ..state import BillState


def llm_correction_node(state: BillState):
    """OCR誤読を修正する（raw_text は上書きしない版）"""

    current_retry = state.get("retry_count", 0)
    providers = ModelFactory.get_llm_list(current_retry)

    template = """
    ### ROLE ###
    You are an OCR correction specialist.
    Fix ONLY OCR mistakes (typos, misread numbers, broken words).
    DO NOT summarize, DO NOT add new info, DO NOT remove content.

    ### RAW OCR TEXT ###
    {raw_text}

    ### OUTPUT ###
    Return ONLY the corrected text.
    """

    prompt = PromptTemplate.from_template(template)

    response = None
    active_model = ""

    for p in providers:
        try:
            llm = ModelFactory.create_instance(p)
            if not llm:
                continue

            chain = prompt | llm
            response = chain.invoke({
                "raw_text": state["raw_text"]
            })

            active_model = p
            break

        except Exception as e:
            print(f"⚠️ LLM correction failed on {p}: {str(e)[:80]}")
            continue

    # 全部失敗 → corrected_text は None のまま
    if not response:
        state["corrected_text"] = None
        state["audit_logs"] = state.get("audit_logs", []) + [
            f"LLM correction failed on all providers (retry={current_retry})"
        ]
        return state

    # 出力クリーンアップ
    content = response.content.strip()
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL).strip()

    # raw_text は上書きしない
    state["corrected_text"] = content

    state["audit_logs"] = state.get("audit_logs", []) + [
        f"LLM correction by {active_model} (retry={current_retry})"
    ]

    return state
