from ..state import BillState

def validation_node(state: BillState):
    data = state.get("extracted_json", {})
    lang = state.get("language", "EN")
    warnings = []
    requires_review = False

    # Example Business Logic: Flag high amounts (>500k JPY or >5k USD)
    amount = float(data.get("AMOUNT", 0))
    if (lang == "JP" and amount > 500000) or (lang == "EN" and amount > 5000):
        msg = "⚠️ 高額な請求です。内容を再確認してください。" if lang == "JP" else "⚠️ High amount detected. Please verify manually."
        warnings.append(msg)
        requires_review = True

    # Check for placeholder IDs
    inv_id = str(data.get("Invoice ID", ""))
    if inv_id in ["001", "123", "N/A", ""]:
        msg = "⚠️ 請求書番号が標準的ではありません。重複に注意してください。" if lang == "JP" else "⚠️ Invoice ID looks generic. Check for duplicates."
        warnings.append(msg)
        requires_review = True

    # Append warnings to the critique text for the UI
    new_critique = state.get("critique", "")
    if warnings:
        new_critique += "\n\n" + "\n".join(warnings)

    return {
        "critique": new_critique,
        "requires_review": requires_review,
        "status": "validation_complete"
    }