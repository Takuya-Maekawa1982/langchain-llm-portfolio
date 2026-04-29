import base64
import pandas as pd
from pypdf import PdfReader
from docx import Document

def extract_raw_content(uploaded_file):
    """
    Standardizes input: 
    - Text-based (PDF, Word, Excel) -> String
    - Image-based (JPG, PNG) -> Base64 String
    """
    ext = uploaded_file.name.split('.')[-1].lower()
    
    if ext in ['jpg', 'jpeg', 'png']:
        return base64.b64encode(uploaded_file.read()).decode("utf-8"), "image"
    
    if ext == 'pdf':
        reader = PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text, "text"
    
    if ext == 'docx':
        doc = Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs]), "text"
    
    if ext == 'xlsx':
        df = pd.read_excel(uploaded_file)
        return df.to_string(index=False), "text"
        
    return None, None