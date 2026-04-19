import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# 1. Fetch the key
api_key = os.getenv("GROQ_API_KEY")

# Check if it exists to avoid errors later
if api_key is None:
    print("Error: GROQ_API_KEY is not set!")
else:
    print("API Key successfully loaded.")
    
# The "Smart" Choice (Best for most LangChain tasks)
llm_model = "llama-3.3-70b-versatile"

# The "Chat" Choice (Best for most LangChain chat tasks)
chat_llm_model = "meta-llama/llama-4-scout-17b-16e-instruct"

# The "Fast" Choice (Best for simple tasks/summarization)
# llm_model = "llama-3.1-8b-instant"

# The "Vision" Choice (If you need to analyze images)
# llm_model = "llama-3.2-90b-vision-preview"

# 2. Initialize the LangChain Wrapper
# It will automatically look for GROQ_API_KEY in your env, 
# but you can also pass it explicitly.
llm = ChatGroq(
    model=llm_model,
    temperature=0.7,
    groq_api_key=api_key # Optional if env var is already set
)

print(llm.invoke("What is the weather in WA DC").content)

# Initialize the chat model
chat = ChatGroq(
    temperature=0.7, 
    model_name=chat_llm_model
)

# Define a conversation
messages = [
    SystemMessage(content="You are a helpful assistant that explains AI concepts simply."),
    HumanMessage(content="How old is universe?")
]

print("======")
# Get the response
response = chat.invoke(messages)
print(response.content)