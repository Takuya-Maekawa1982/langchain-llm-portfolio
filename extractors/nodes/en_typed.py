import re
import json
from langchain_core.prompts import PromptTemplate
from utils.models import ModelFactory
from ..state import BillState

def en_extractor_node(state: BillState):
    current_retry = state.get("retry_count", 0)
    feedback = state.get("critique", "")
    
    # 1. Fallback priority list
    providers = ModelFactory.get_llm_list(current_retry)
    
    # 2. Feedback build
    feedback_section = f"\n### PREVIOUS AUDIT FEEDBACK (FIX THIS) ###\n{feedback}" if feedback and "RETRY" in feedback.upper() else ""

    # 3. Prompt Template (Use double braces ONLY inside the template string)
    template = """
    ### ROLE ###
    Senior Data Engineer. Extract invoice data into structured JSON with 100% accuracy.

    ### STRICT TYPE DEFINITION ###
    {{
        "Invoice ID": "string",
        "Issue Date": "string (YYYY-MM-DD)",
        "DESCRIPTION": "string",
        "UNIT PRICE": "number (float)",
        "AMOUNT": "number (float)",
        "Bill For": "string (Full Name, Address, and Phone/Tel/PH)",
        "From": "string (Full Vendor Name, Address, and Phone/Tel/PH)",
        "Terms": "string"
    }}

    ### FEW-SHOT EXAMPLES ###
    Example 1: Standard Service (Telecom)
    RAW: 
    Invoice #2,389 | Nov 27, 2026 | Terms: Net 30
    From: Global Telecom Solutions | 1583 Tanneba St, WA | Tel: 590-327-3987
    Bill To: Paul Regex | 1110 West 11th Ave, Suite 896 | Phone: 128-764-9411
    Monthly Data Plan: $500.00 | Total: $500.00
    JSON:
    {{
        "Invoice ID": "2,389",
        "Issue Date": "2026-11-27",
        "DESCRIPTION": "Monthly Data Plan",
        "UNIT PRICE": 500.0,
        "AMOUNT": 500.0,
        "Bill For": "Paul Regex, 1110 West 11th Ave, Suite 896 | Phone: 128-764-9411",
        "From": "Global Telecom Solutions, 1583 Tanneba St, WA | Tel: 590-327-3987",
        "Terms": "Net 30"
    }}

    Example 2: Retail / Goods
    RAW: 
    Order: 9982 | Date: 2026/04/20 | Terms: Due on Receipt
    Vendor: General Supply Store | 888 Industrial Rd | TEL: 03-1234-5678
    Ship To: Jane Doe | 12 Maple St, Springfield | PH: 090-9876-5432
    Items: Maintenance Equipment | Amt: 5,400.00
    JSON:
    {{
        "Invoice ID": "9982",
        "Issue Date": "2026-04-20",
        "DESCRIPTION": "Maintenance Equipment",
        "UNIT PRICE": 5400.0,
        "AMOUNT": 5400.0,
        "Bill For": "Jane Doe, 12 Maple St, Springfield | PH: 090-9876-5432",
        "From": "General Supply Store, 888 Industrial Rd | TEL: 03-1234-5678",
        "Terms": "Due on Receipt"
    }}

    {feedback_section}

    ### SOURCE RAW TEXT ###
    {pages}

    ### JSON OUTPUT (STRICTLY JSON ONLY) ###
    """
    prompt_template = PromptTemplate.from_template(template)

    # 4. Execution Loop (Fallback for 429 errors)
    response = None
    active_model = ""

# for debug
    # for p in providers:
    #     print("Trying provider:", p)
    #     try:
    #         llm = ModelFactory.create_instance(p)
    #         print("LLM instance:", llm)

    #         chain = prompt_template | llm
    #         response = chain.invoke({
    #             "pages": state["raw_content"],
    #             "feedback_section": feedback_section
    #         })
    #         print("SUCCESS with:", p)
    #         active_model = p
    #         break

    #     except Exception as e:
    #         print("❌ ERROR with", p, ":", e)
    #         continue
    
    
    for p in providers:
        try:
            llm = ModelFactory.create_instance(p)
            if not llm: continue
            
            chain = prompt_template | llm
            response = chain.invoke({
                "pages": state["raw_content"], 
                "feedback_section": feedback_section
            })
            active_model = p
            break 
        except Exception as e:
            print(f"⚠️ {p} extraction failed: {str(e)[:50]}")
            continue

    # --- Python Dictionary Return (MUST use single braces) ---
    if not response:
        return {"extracted_json": {"error": "All providers failed (Rate Limit)"}}

    # 5. Parsing
    content = response.content.strip()
    content = re.sub(r'```json\s?|```', '', content).strip()
    match = re.search(r'\{.*\}', content, re.DOTALL)
    
    data_dict = {}
    if match:
        try:
            json_str = match.group(0).strip()
            data_dict = json.loads(json_str)
        except Exception as e:
            data_dict = {"error": "JSON Parsing failed", "raw": content[:100]}
    else:
        data_dict = {"error": "No JSON found", "raw": content[:100]}

    return {
        "extracted_json": data_dict,
        "audit_logs": [f"Step {current_retry} (EN): Extracted by {active_model}"]
    }