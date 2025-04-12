import os
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
from portia.open_source_tools.local_file_reader_tool import FileReaderTool
from portia.open_source_tools.llm_tool import LLMTool
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

    def run(self, context: ExecutionContext, json_file_path: str) -> str:
        """Run the Lab Results Tool."""
        try:
            # Create instances of the tools
            file_reader = FileReaderTool()
            llm_tool = LLMTool()
            
            # Read the lab results file
            lab_results = file_reader.run(context, json_file_path)
            
            # Create prompt for LLM analysis
            prompt = f"""
            You are a medical professional analyzing lab test results. Please analyze these results:

            {lab_results}

            Please provide a comprehensive analysis that includes:
            1. A clear explanation of what each test measures and its significance
            2. Analysis of whether any values appear abnormal based on standard medical reference ranges
            3. Potential causes for any abnormal values
            4. Recommended follow-up actions or lifestyle changes
            5. Any health concerns that should be discussed with a healthcare provider

            Write in clear, patient-friendly language while maintaining medical accuracy.
            Format your response as a detailed medical report with sections for:
            - Overview
            - Test-by-test analysis
            - Abnormal findings
            - Recommendations
            - Follow-up actions

            Do not include any introductory phrases like "I will analyze" - just provide the analysis directly.
            """
            
            # Get LLM analysis
            analysis = llm_tool.run(context, prompt)
            return analysis
            
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
            "Analyze the lab results from src/data/patient_data.json and provide a comprehensive explanation. "
            "If any of the values suggest a specific health issue, please diagnose it and suggest next steps "
            "to bring up with a professional health care provider."
        )
        
        print("\nHere are the steps in the generated plan:")
        [print(step.model_dump_json(indent=2)) for step in plan.steps]

        if os.getenv("CI") != "true":
            user_input = input("Are you happy with the plan? (y/n):\n")
            if user_input != "y":
                exit(1)

        run = portia.run_plan(plan)
        
        if run.state == PlanRunState.COMPLETE:
            # Print available keys to help debug
            print("\nAvailable output keys:")
            for key in run.outputs.step_outputs.keys():
                print(f"- {key}")
            
            # Try to get the lab results analysis from the first available output
            if run.outputs.step_outputs:
                first_key = next(iter(run.outputs.step_outputs))
                lab_results = run.outputs.step_outputs[first_key].value
                print("\nLab Results Analysis:")
                print(lab_results)
            else:
                print("No outputs found in the plan run")
        else:
            raise Exception(
                f"Plan run failed with state {run.state}. Check logs for details."
            )