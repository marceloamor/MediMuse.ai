import os
import json
from typing import Dict, Any, List
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

class LabResult(BaseModel):
    """Individual lab test result with interpretation."""
    test_name: str
    value: float
    interpretation: str
    reference_range: str = Field(default="Not available")
    significance: str = Field(default="Not available")

class LabResultsAnalysis(BaseModel):
    """Structured analysis of lab results."""
    patient_summary: Dict[str, Any]
    test_analysis: List[LabResult]
    overall_assessment: str
    recommendations: List[str]
    follow_up_actions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the analysis to a dictionary for JSON serialization."""
        return {
            "patient_summary": self.patient_summary,
            "test_analysis": [test.model_dump() for test in self.test_analysis],
            "overall_assessment": self.overall_assessment,
            "recommendations": self.recommendations,
            "follow_up_actions": self.follow_up_actions
        }

class LabResultsToolSchema(BaseModel):
    """Input for LabResultsTool."""
    json_file_path: str = Field(
        ...,
        description="Path to the JSON file containing lab results.",
    )

class LabResultsTool(Tool[Dict[str, Any]]):
    """Analyzes and explains lab results from a JSON file."""

    id: str = "lab_results_tool"
    name: str = "Lab Results Tool"
    description: str = "Analyzes and explains blood test or lab results in plain language, providing detailed interpretations and recommendations."
    args_schema: type[BaseModel] = LabResultsToolSchema
    output_schema: tuple[str, str] = (
        "Dict[str, Any]",
        "A structured analysis of the lab results including interpretations and recommendations.",
    )

    def _parse_lab_results(self, json_file_path: str) -> Dict[str, Any]:
        """Parse lab results from JSON file."""
        try:
            # hard code the file path for now
            json_file_path = "src/data/patient_data.json"
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Lab results file not found: {json_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {json_file_path}")

    def _analyze_test_result(self, test_name: str, value: float) -> Dict[str, str]:
        """Analyze a single test result using the LLM."""
        prompt = f"""
        You are a medical professional analyzing lab test results. Please analyze this specific test result:

        Test: {test_name}
        Value: {value}

        Please provide a detailed analysis including:
        1. The normal reference range for this test
        2. Interpretation of this specific value
        3. Clinical significance and potential implications

        Format your response as a JSON object with these exact keys:
        {{
            "reference_range": "the normal range for this test",
            "interpretation": "your interpretation of this value",
            "significance": "clinical significance and implications"
        }}
        """
        
        try:
            # This will be replaced with actual LLM call in the run method
            return {
                "reference_range": "To be determined by LLM",
                "interpretation": "To be determined by LLM",
                "significance": "To be determined by LLM"
            }
        except Exception as e:
            print(f"Error analyzing test {test_name}: {str(e)}")
            return {
                "reference_range": "Error: Could not determine reference range",
                "interpretation": "Error: Could not interpret result",
                "significance": "Error: Could not determine significance"
            }

    def _generate_overall_assessment(self, lab_results: Dict[str, Any], test_analysis: List[LabResult]) -> str:
        """Generate overall assessment using the LLM."""
        # Format test results for the prompt
        test_results_str = "\n".join([
            f"- {test.test_name}: {test.value} (Reference: {test.reference_range})"
            for test in test_analysis
        ])
        
        prompt = f"""
        You are a medical professional providing an overall assessment of lab results.

        Patient Information:
        - Name: {lab_results.get('PatientName', 'Not provided')}
        - Age: {lab_results.get('PatientAge', 'Not provided')}
        - Gender: {lab_results.get('PatientSex', 'Not provided')}
        - Weight: {lab_results.get('PatientWeight', 'Not provided')} kg

        Test Results:
        {test_results_str}

        Please provide a comprehensive overall assessment that:
        1. Summarizes the key findings
        2. Identifies any concerning patterns or values
        3. Discusses potential health implications
        4. Suggests next steps

        Write in clear, patient-friendly language while maintaining medical accuracy.
        """
        
        try:
            # This will be replaced with actual LLM call in the run method
            return "To be determined by LLM"
        except Exception as e:
            print(f"Error generating overall assessment: {str(e)}")
            return "Error: Could not generate overall assessment"

    def run(self, context: ExecutionContext, json_file_path: str) -> Dict[str, Any]:
        """Run the Lab Results Tool."""
        try:
            # Parse lab results
            lab_results = self._parse_lab_results(json_file_path)
            
            # Extract patient information
            patient_info = {
                "name": lab_results.get('PatientName', 'Not provided'),
                "age": lab_results.get('PatientAge', 'Not provided'),
                "gender": lab_results.get('PatientSex', 'Not provided'),
                "weight": lab_results.get('PatientWeight', 'Not provided')
            }
            
            # Analyze each test result
            test_analysis = []
            for test_name, value in lab_results.items():
                if test_name not in ['PatientName', 'PatientSex', 'PatientAge', 'PatientWeight']:
                    # Get LLM response for test analysis
                    analysis_prompt = f"""
                    You are a medical professional analyzing lab test results. Please analyze this specific test result:

                    Test: {test_name}
                    Value: {value}

                    Please provide a detailed analysis including:
                    1. The normal reference range for this test
                    2. Interpretation of this specific value
                    3. Clinical significance and potential implications

                    Format your response as a JSON object with these exact keys:
                    {{
                        "reference_range": "the normal range for this test",
                        "interpretation": "your interpretation of this value",
                        "significance": "clinical significance and implications"
                    }}
                    """
                    analysis_response = context.llm.complete(analysis_prompt)
                    analysis = json.loads(analysis_response)
                    
                    test_analysis.append(LabResult(
                        test_name=test_name,
                        value=value,
                        interpretation=analysis["interpretation"],
                        reference_range=analysis["reference_range"],
                        significance=analysis["significance"]
                    ))
            
            # Format test results for the overall assessment
            test_results_str = "\n".join([
                f"- {test.test_name}: {test.value} (Reference: {test.reference_range})"
                for test in test_analysis
            ])
            
            # Generate overall assessment
            assessment_prompt = f"""
            You are a medical professional providing an overall assessment of lab results.

            Patient Information:
            - Name: {lab_results.get('PatientName', 'Not provided')}
            - Age: {lab_results.get('PatientAge', 'Not provided')}
            - Gender: {lab_results.get('PatientSex', 'Not provided')}
            - Weight: {lab_results.get('PatientWeight', 'Not provided')} kg

            Test Results:
            {test_results_str}

            Please provide a comprehensive overall assessment that:
            1. Summarizes the key findings
            2. Identifies any concerning patterns or values
            3. Discusses potential health implications
            4. Suggests next steps

            Write in clear, patient-friendly language while maintaining medical accuracy.
            """
            overall_assessment = context.llm.complete(assessment_prompt)
            
            # Generate recommendations and follow-up actions
            recommendations = [
                "Schedule a follow-up appointment with your healthcare provider",
                "Discuss any abnormal values with your doctor",
                "Consider lifestyle modifications based on the results"
            ]
            
            follow_up_actions = [
                "Review results with primary care physician",
                "Schedule any necessary follow-up tests",
                "Implement recommended lifestyle changes"
            ]
            
            # Create analysis and convert to dictionary
            analysis = LabResultsAnalysis(
                patient_summary=patient_info,
                test_analysis=test_analysis,
                overall_assessment=overall_assessment,
                recommendations=recommendations,
                follow_up_actions=follow_up_actions
            )
            
            return analysis.to_dict()
            
        except Exception as e:
            raise Exception(f"Error processing lab results: {str(e)}")

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
            "Analyze the lab results from the patient data file and provide a comprehensive explanation. "
            "Include detailed interpretations of each test, overall health assessment, and specific recommendations."
        )
        
        print("\nHere are the steps in the generated plan:")
        [print(step.model_dump_json(indent=2)) for step in plan.steps]

        run = portia.run_plan(plan)
        
        # Print the structured results
        if run.state == PlanRunState.COMPLETE:
            # Get the lab results analysis from the step outputs
            lab_results = run.outputs.step_outputs["$lab_results_analysis"].value
            print("\nLab Results Analysis:")
            print(lab_results)  # The value is already a JSON string
        else:
            raise Exception(
                f"Plan run failed with state {run.state}. Check logs for details."
            )