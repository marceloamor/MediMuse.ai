import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from portia import (
    Config,
    DefaultToolRegistry,
    ExecutionContext,
    InMemoryToolRegistry,
    LLMModel,
    LogLevel,
    PlanRunState,
    Portia,
    Tool,
    execution_context,
)
from portia.cli import CLIExecutionHooks
from pydantic import BaseModel, Field

load_dotenv()

# Load API keys from environment
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PORTIA_API_KEY = os.getenv('PORTIA_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

if not all([GOOGLE_API_KEY, PORTIA_API_KEY, TAVILY_API_KEY]):
    raise ValueError("Missing required API keys in environment variables")

class LabResultsToolSchema(BaseModel):
    """Input for LabResultsTool."""
    json_file_path: str = Field(
        ...,
        description="Path to the JSON file containing lab results.",
    )

class LabResultsTool(Tool[str]):
    """Analyzes and explains lab results from a JSON file."""

    id: str = "lab_results_tool"
    name: str = "Lab Results Tool"
    description: str = "Analyzes and explains blood test or lab results in plain language."
    args_schema: type[BaseModel] = LabResultsToolSchema
    output_schema: tuple[str, str] = (
        "str",
        "A detailed explanation of the lab results.",
    )

    def _parse_lab_results(self, json_file_path: str) -> Dict[str, Any]:
        """Parse lab results from JSON file."""
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Lab results file not found: {json_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {json_file_path}")

    def _generate_prompt(self, lab_results: Dict[str, Any]) -> str:
        """Generate a prompt for the LLM based on lab results."""
        # Build patient information section
        patient_info = f"""
Patient Information:
- Name: {lab_results.get('PatientName', 'Not provided')}
- Age: {lab_results.get('PatientAge', 'Not provided')}
- Gender: {lab_results.get('PatientSex', 'Not provided')}
- Weight: {lab_results.get('PatientWeight', 'Not provided')} kg
"""

        # Build lab results section
        lab_results_section = "\nLab Results:\n"
        for test_name, value in lab_results.items():
            if test_name not in ['PatientName', 'PatientSex', 'PatientAge', 'PatientWeight']:
                lab_results_section += f"- {test_name}: {value}\n"

        prompt = f"""
Please analyze these lab results and provide a comprehensive explanation:

{patient_info}
{lab_results_section}

Please provide:
1. A clear explanation of what each test measures and its significance
2. Analysis of whether any values appear abnormal based on standard medical reference ranges
3. Potential causes for any abnormal values
4. Recommended follow-up actions or lifestyle changes
5. Any health concerns that should be discussed with a healthcare provider

Please use your medical knowledge to interpret these results and provide a detailed, patient-friendly explanation.
"""

        return prompt

    def run(self, _: ExecutionContext, json_file_path: str) -> str:
        """Run the Lab Results Tool."""
        try:
            #  hard code the json file path for now 
            json_file_path = "src/data/patient_data.json"
            # Parse lab results from JSON file
            lab_results = self._parse_lab_results(json_file_path)
            
            # Generate prompt
            prompt = self._generate_prompt(lab_results)
            
            return prompt
            
        except Exception as e:
            return f"Error processing lab results: {str(e)}"

# Configure Portia with all API keys
config = Config.from_default(
    llm_model_name=LLMModel.GEMINI_2_0_FLASH,
    default_log_level=LogLevel.DEBUG,
    google_api_key=GOOGLE_API_KEY,
    portia_api_key=PORTIA_API_KEY,
    tavily_api_key=TAVILY_API_KEY
)

# Set up tools
tools = DefaultToolRegistry(config) + InMemoryToolRegistry.from_local_tools(
    [LabResultsTool()]
)

# Instantiate Portia
portia = Portia(
    config=config,
    tools=tools,
    execution_hooks=CLIExecutionHooks(),
)

# Example usage
if __name__ == "__main__":
    with execution_context(
        end_user_id="lab-results-analyzer",
    ):
        # Plan and run the analysis
        plan = portia.plan(
            "Analyze the lab results from the patient data file and provide a comprehensive explanation. If any of the values suggest a specific health issue, please diagnose it and suggest next steps to bring up with a professional health care provider."
        )
        
        print("\nHere are the steps in the generated plan:")
        [print(step.model_dump_json(indent=2)) for step in plan.steps]

        if os.getenv("CI") != "true":
            user_input = input("Are you happy with the plan? (y/n):\n")
            if user_input != "y":
                exit(1)

        run = portia.run_plan(plan)

        if run.state != PlanRunState.COMPLETE:
            raise Exception(
                f"Plan run failed with state {run.state}. Check logs for details."
            )