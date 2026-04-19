import streamlit as st
import sys
import os
import importlib.util

st.set_page_config(page_title="Takuya's AI Toolbox", layout="wide")

st.sidebar.title("Projects")
selection = st.sidebar.radio("Go to:", ["Home", "Bill extractor", "Hand-Written Bill extractor"])

# Helper function to load modules from complex paths
def load_module(module_name, relative_path):
    path = os.path.join(os.getcwd(), relative_path)
    if path not in sys.path:
        sys.path.append(path)
    
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(path, "logic.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if selection == "Home":
    st.title("Welcome")
    st.write("Select a tool from the sidebar to begin.")

elif selection == "Bill extractor":
    # Handles the complex path and hyphenated folder names
    extractor = load_module("extractor", "langchain-course-code/projects/extractor")
    extractor.run()

elif selection == "Hand-Written Bill extractor":
    # Handles the complex path and hyphenated folder names
    hw_extractor = load_module("hw_extractor", "langchain-course-code/projects/hand-written-bill-extractor")
    hw_extractor.run()