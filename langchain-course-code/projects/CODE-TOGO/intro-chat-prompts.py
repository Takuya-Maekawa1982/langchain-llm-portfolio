import os
from langchain_groq import ChatGroq

# NEW: Import from langchain_core instead of langchain.prompts
from langchain_core.prompts import PromptTemplate

# NEW: Legacy chains like LLMChain are now in langchain.chains 
# (Note: Some 2026 versions moved this to 'langchain_classic')
try:
    from langchain.chains import LLMChain
except ImportError:
    from langchain_classic.chains import LLMChain

# 1. Setup
api_key = os.getenv("GROQ_API_KEY")
llm_model = "llama-3.3-70b-versatile"

# 2. Initialize Groq
groq_llm = ChatGroq(temperature=0.7, model=llm_model)

# 3. Define Prompt
prompt = PromptTemplate(
    input_variables=["language"],
    template="How do you say good morning in {language}"
)

# 4. Define and Run Chain
chain = LLMChain(llm=groq_llm, prompt=prompt)
print(chain.run(language="German"))