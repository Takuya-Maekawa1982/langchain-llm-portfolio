import os
import re
import json
import pandas as pd
import streamlit as st
from pypdf import PdfReader
from dotenv import find_dotenv, load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv(find_dotenv())

# Extract text from PDF
def get_pdf_text(pdf_doc):
    text = ""
    pdf_reader = PdfReader(pdf_doc)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Extract structured data using Multi-Shot and Strict Instructions
def extracted_data(pages_data):
    template = """
    ### SYSTEM INSTRUCTIONS ###
    Extract invoice data into a single JSON object. 
    - STRICT KEYS: Use ONLY "Invoice ID", "DESCRIPTION", "Issue Date", "UNIT PRICE", "AMOUNT", "Bill For", "From", "Terms".
    - NO VARIATIONS: Do not use "Amount", "Total", or "sub-total".
    - NUMERIC ONLY: For "AMOUNT" and "UNIT PRICE", DO NOT include "$" or commas. Use only digits and decimals (e.g., 500.00).
    - ADDRESS FORMAT: Combine Name, Full Address, and Telephone Number into one single string for "Bill For" and "From".
    - OUTPUT: Return ONLY a valid JSON object.

    ### EXAMPLE 1 ###
    INPUT: "Inv #101. Date 01/01/2026. From: TechCorp, 555 Main St. To: Alice Smith, 123 Lane, tel # 555-0199. Total: $150.00"
    OUTPUT: {{
        "Invoice ID": "101",
        "DESCRIPTION": "Services",
        "Issue Date": "01/01/2026",
        "UNIT PRICE": "150.00",
        "AMOUNT": "150.00",
        "Bill For": "Alice Smith, 123 Lane, tel # 555-0199",
        "From": "TechCorp, 555 Main St",
        "Terms": "N/A"
    }}

    ### EXAMPLE 2 ###
    INPUT: "Bill For: Paul Regex, 1110 112THAVE W, SUITE 89626, SATURNEY, WA 99765. Contact: tel # 12876494. Amount: $500.00. ID: 2,389."
    OUTPUT: {{
        "Invoice ID": "2,389",
        "DESCRIPTION": "Phone bill",
        "Issue Date": "11/27/2026",
        "UNIT PRICE": "500.00",
        "AMOUNT": "500.00",
        "Bill For": "Paul Regex, 1110 112THAVE W, SUITE 89626, SATURNEY, WA 99765, tel # 12876494",
        "From": "DR-TeleP, 1583 E. TanneVa Ln, Nekaspo, WE 99010",
        "Terms": "Due on Receipt"
    }}

    ### ACTUAL TEXT TO PROCESS ###
    {pages}

    ### JSON RESPONSE ###
    """
    
    prompt_template = PromptTemplate.from_template(template)
    llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")
    
    chain = prompt_template | llm
    response = chain.invoke({"pages": pages_data})
    
    return response.content

# Create DataFrame from PDFs
def create_docs(user_pdf_list):
    cols = ['Invoice ID', 'DESCRIPTION', 'Issue Date', 'UNIT PRICE', 'AMOUNT', 'Bill For', 'From', 'Terms']
    df = pd.DataFrame(columns=cols)

    for pdf_file in user_pdf_list:
        try:
            raw_data = get_pdf_text(pdf_file)
            llm_extracted_data = extracted_data(raw_data)

            # Use regex to isolate the JSON block
            match = re.search(r'(\{.*\})', llm_extracted_data, re.DOTALL)

            if match:
                data_dict = json.loads(match.group(1))
                
                # Create row and align to target columns
                new_row = pd.DataFrame([data_dict]).reindex(columns=cols)
                
                # Double-check cleanup just in case LLM missed the instruction
                if 'AMOUNT' in new_row.columns:
                    new_row['AMOUNT'] = new_row['AMOUNT'].astype(str).str.replace(r'[\$,]', '', regex=True)

                df = pd.concat([df, new_row], ignore_index=True)
            else:
                st.error(f"Could not find structured data for {pdf_file.name}")
        
        except Exception as e:
            st.error(f"Error processing {pdf_file.name}: {e}")

    return df