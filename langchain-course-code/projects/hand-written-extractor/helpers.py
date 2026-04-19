import os
import io
import json
import re
import requests
import base64
import pandas as pd
import streamlit as st
from pdf2image import convert_from_bytes

# Configuration for Llama 3.2 Vision via Hugging Face
# Make sure your HF_TOKEN is set in your .env file or environment variables
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-11B-Vision-Instruct"
HF_TOKEN = os.getenv("HF_TOKEN")

def query_vlm(image_bytes, prompt):
    """Sends encoded image to Hugging Face Inference API."""
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    payload = {
        "model": "meta-llama/Llama-3.2-11B-Vision-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "parameters": {"max_new_tokens": 700, "temperature": 0.01}
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

def extracted_data(pdf_file):
    """Converts PDF to image and extracts structured data using a VLM."""
    pdf_file.seek(0)
    
    # --- AUTOMATION FIX: Hardcoded Poppler Path for Windows ---
    # This ensures the 'Unable to get page count' error is resolved on Windows PCs
    # using the Chocolatey installation path.
    CHOCO_POPPLER_PATH = r'C:\ProgramData\chocolatey\bin'
    
    try:
        if os.name == 'nt':  # If running on Windows
            images = convert_from_bytes(pdf_file.read(), poppler_path=CHOCO_POPPLER_PATH)
        else:
            images = convert_from_bytes(pdf_file.read())
    except Exception as e:
        st.error(f"PDF Conversion Error: {e}")
        return ""

    # Prepare image for API
    img_byte_arr = io.BytesIO()
    images[0].save(img_byte_arr, format='PNG')
    image_bytes = img_byte_arr.getvalue()

    # MULTI-SHOT PROMPT: Explicitly trained on the Paul Regex / Rental-bill layout
    prompt = """
    ### INSTRUCTION ###
    Extract invoice data from the image into a single JSON object.
    
    ### RULES ###
    1. STRICT KEYS: "Invoice ID", "DESCRIPTION", "Issue Date", "UNIT PRICE", "AMOUNT", "Bill For", "From", "Terms"
    2. ADDRESSES: Combine Name, Full Address, and Phone Number into one string for "Bill For" and "From".
    3. NUMERIC: Remove "$" and commas from "AMOUNT" and "UNIT PRICE".
    4. HANDWRITTEN TESTS: If a field is empty (like a handwritten total), use "".
    5. OUTPUT: Return ONLY the JSON block. Do not provide explanations.

    ### EXAMPLE (Rental Layout) ###
    INPUT: A scanned invoice with handwritten blanks and multi-line address.
    OUTPUT: {
        "Invoice ID": "1000",
        "DESCRIPTION": "Condo Rental",
        "Issue Date": "11/27/2026",
        "UNIT PRICE": "2500.00",
        "AMOUNT": "",
        "Bill For": "Paul Regex, 1110 112THAVE W, SUITE 89626, SATURNEY, WA 99765, tel # 12876494",
        "From": "DR-TeleP, 1583 E. TanneVa Ln, Nekaspo, WE 99010, tel # 590-327-3987",
        "Terms": "Due upon receipt"
    }

    ### ACTUAL DATA ###
    Process the provided image following the pattern above.
    """
    
    response_data = query_vlm(image_bytes, prompt)
    
    # Extract the text content from the API response
    if isinstance(response_data, list) and len(response_data) > 0:
        return response_data[0].get("generated_text", "")
    elif isinstance(response_data, dict):
        if "choices" in response_data:
            return response_data["choices"][0]["message"]["content"]
        return response_data.get("generated_text", "")
    return ""

def create_docs(user_pdf_list):
    """Processes multiple PDFs into a single pandas DataFrame."""
    cols = ['Invoice ID', 'DESCRIPTION', 'Issue Date', 'UNIT PRICE', 'AMOUNT', 'Bill For', 'From', 'Terms']
    df = pd.DataFrame(columns=cols)

    for pdf_file in user_pdf_list:
        try:
            llm_response = extracted_data(pdf_file)
            # Find JSON block in the model's text response
            match = re.search(r'(\{.*\})', llm_response, re.DOTALL)
            
            if match:
                data_dict = json.loads(match.group(1))
                # Ensure all 8 columns exist, even if LLM missed one
                filtered_dict = {k: data_dict.get(k, "") for k in cols}
                new_row = pd.DataFrame([filtered_dict])
                
                # Standardize numeric values
                if 'AMOUNT' in new_row.columns:
                    new_row['AMOUNT'] = new_row['AMOUNT'].astype(str).str.replace(r'[^\d.]', '', regex=True)
                
                df = pd.concat([df, new_row], ignore_index=True)
        except Exception as e:
            st.error(f"Failed to process {pdf_file.name}: {e}")
            
    return df   