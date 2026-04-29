import os
import streamlit as st

def get_key(name, required=True):
    """
    Retrieves keys from:
    1. System Environment (Local PC / Codespaces)
    2. Streamlit Secrets (Hugging Face / Streamlit Cloud)
    """
    # 1. Try System Environment first (Local Surface Pro)
    key = os.getenv(name)
    
    # 2. Try Streamlit Secrets if not in env (Cloud Hosting)
    if not key:
        try:
            key = st.secrets.get(name)
        except:
            key = None

    # 3. Validation Logic
    if not key and required:
        # If in a Streamlit App, show a UI error and stop
        try:
            st.error(f"🔑 **Missing Secret:** `{name}` is not set.")
            st.info("Check your Windows User Environment Variables (Local) or HF Secrets (Cloud).")
            st.stop()
        except:
            # If running as a plain script, raise a standard error
            raise ValueError(f"CRITICAL: Environment variable {name} is missing.")
            
    return key