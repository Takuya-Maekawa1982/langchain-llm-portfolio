from typing import TypedDict, Annotated, List
from operator import add

class BillState(TypedDict):
    file_name: str
    content_type: str
    raw_content: str
    language: str 
    is_handwritten: bool 
    extracted_json: dict
    
    # Controls
    audit_mode: bool
    validate_mode: bool
    max_retries: int 
    
    # Reducers
    # retry_count: Ints will be added (0 + 1 + 1...)
    retry_count: Annotated[int, add] 
    
    # critique: Strings will be overwritten (Latest only for LLM focus)
    critique: Annotated[str, lambda old, new: new] 
    
    # audit_logs: Lists will be concatenated (Cumulative for Human audit)
    audit_logs: Annotated[List[str], add] 
    audit_summary: Annotated[str, lambda old, new: new]
    requires_review: Annotated[bool, lambda old, new: new] 
    
    status: str