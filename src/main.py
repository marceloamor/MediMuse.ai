import os
from dotenv import load_dotenv
from portia import (
    Config,
    LLMModel,
    LLMProvider,
    Portia,
    example_tool_registry,
)

#from tools.ExplainLabResults import ExplainLabResults

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Create a default Portia config with LLM provider set to Google GenAI and model set to Gemini 2.0 Flash
google_config = Config.from_default(
    llm_provider=LLMProvider.GOOGLE_GENERATIVE_AI,
    llm_model_name=LLMModel.GEMINI_2_0_FLASH,
    google_api_key=GOOGLE_API_KEY
)
# Instantiate a Portia instance. Load it with the config and with the example tools.
portia = Portia(config=google_config, tools=example_tool_registry)
# Run the test query and print the output!
query = 'I have a lab result of 120 mg/dL for cholesterol, and a lab result of 100 mg/dL for HDL cholesterol. What is my cholesterol ratio? What does this mean for me and my health and diet?'
plan_run = portia.run(query)
print(plan_run.model_dump_json(indent=2))