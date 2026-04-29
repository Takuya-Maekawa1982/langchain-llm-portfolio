from langgraph.graph import StateGraph, END
from .state import BillState

# --- Preprocessing ---
from .nodes.lang_detector import lang_detector_node

# --- Extraction ---
from .nodes.en_typed import en_extractor_node
from .nodes.jp_typed import jp_extractor_node

# --- Postprocessing ---
from .nodes.critiquer import critique_node
from .nodes.validator import validation_node
from .nodes.summarizer import summarizer_node


# --- Routing Logic ---
def route_language(state: BillState):
    return "japanese" if state.get("language") == "JP" else "english"


def route_critique(state: BillState):
    if state.get("audit_mode") and "RETRY" in state.get("critique", "").upper():
        if state.get("retry_count", 0) < state.get("max_retries", 0):
            return "retry_jp" if state.get("language") == "JP" else "retry_en"
    return "validate" if state.get("validate_mode") else "finish"


# --- Graph Definition ---
def build_graph():
    workflow = StateGraph(BillState)

    # Preprocessing
    workflow.add_node("lang_detector", lang_detector_node)

    # Extraction
    workflow.add_node("en_extractor", en_extractor_node)
    workflow.add_node("jp_extractor", jp_extractor_node)

    # Postprocessing
    workflow.add_node("critiquer", critique_node)
    workflow.add_node("validator", validation_node)
    workflow.add_node("summarizer", summarizer_node)

    workflow.set_entry_point("lang_detector")

    # 言語ルーティング（LLM Correction は外部で済ませる）
    workflow.add_conditional_edges("lang_detector", route_language, {
        "english": "en_extractor",
        "japanese": "jp_extractor",
    })

    # Extractor → critique
    workflow.add_edge("en_extractor", "critiquer")
    workflow.add_edge("jp_extractor", "critiquer")

    # Critique routing
    workflow.add_conditional_edges("critiquer", route_critique, {
        "retry_en": "en_extractor",
        "retry_jp": "jp_extractor",
        "validate": "validator",
        "finish": "summarizer",
    })

    workflow.add_edge("validator", "summarizer")
    workflow.add_edge("summarizer", END)

    return workflow.compile()


bill_agent = build_graph()
