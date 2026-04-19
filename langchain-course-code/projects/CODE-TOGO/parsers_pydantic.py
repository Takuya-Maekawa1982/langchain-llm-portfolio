import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
# In 2026, we use standard Pydantic v2 or the core wrapper
from pydantic import BaseModel, Field, field_validator
from typing import List

# 1. Load Environment Variables
#api_key = os.getenv("GROQ_API_KEY")
# No need for openai.api_key; ChatGroq looks for GROQ_API_KEY automatically

# 2. Setup Groq Model
# Llama 3.3 70B is highly reliable for structured data extraction
llm_model = "llama-3.3-70b-versatile"
chat = ChatGroq(temperature=0.7, model=llm_model)

email_response = """
Here's our itinerary for our upcoming trip to Europe.
There will be 5 of us on this vacation trip.
We leave from Denver, Colorado airport at 8:45 pm, and arrive in Amsterdam 10 hours later
at Schipol Airport.
We'll grab a ride to our airbnb and maybe stop somewhere for breakfast before 
taking a nap.

Some sightseeing will follow for a couple of hours. 
We will then go shop for gifts 
to bring back to our children and friends.  

The next morning, at 7:45am we'll drive to to Belgium, Brussels - it should only take aroud 3 hours.
While in Brussels we want to explore the city to its fullest - no rock left unturned!
"""

# 3. Define Pydantic Model (Data Structure)
class VacationInfo(BaseModel):
    leave_time: str = Field(description="When they are leaving. Usually a specific time.")
    leave_from: str = Field(description="Departure airport, city, or state.")
    cities_to_visit: List[str] = Field(description="List of cities/towns they will visit.")
    num_people: int = Field(description="Number of people on the trip.")
    
    # Modern Pydantic v2 validator
    @field_validator('num_people')
    @classmethod
    def check_num_people(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Number of people must be greater than 0")
        return v

# 4. Setup Parser and Prompt
pydantic_parser = PydanticOutputParser(pydantic_object=VacationInfo)
format_instructions = pydantic_parser.get_format_instructions()

email_template_revised = """
From the following email, extract the following information regarding 
this trip.

email: {email}

{format_instructions}
"""

updated_prompt = ChatPromptTemplate.from_template(template=email_template_revised)

# 5. Execute Chain
# We use the modern 'invoke' method instead of calling the object directly
messages = updated_prompt.format_prompt(
    email=email_response,
    format_instructions=format_instructions
)

format_response = chat.invoke(messages)

# 6. Parse and Print
vacation = pydantic_parser.parse(format_response.content)

print(f"Data Type: {type(vacation)}")
print(f"Number of People: {vacation.num_people}")
for item in vacation.cities_to_visit:
    print(f"City: {item}")