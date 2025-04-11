import json
import os
from typing import Dict, Any
from portia import Tool

class ExplainLabResults(Tool):
    name: str = "explain_lab_result"
    description: str = "Explains blood test or lab result in plain language and its significance. Input should be a path to a JSON file containing lab results."

    def __init__(self):
        super().__init__()

    def _parse_lab_results(self, json_file_path: str) -> Dict[str, Any]:
        """
        Parse lab results from JSON file.
        """
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Lab results file not found: {json_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {json_file_path}")

    def _generate_prompt(self, lab_results: Dict[str, Any]) -> str:
        """
        Generate a prompt for the LLM based on lab results.
        """
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

    def run(self, input: str) -> str:
        """
        Process lab results from a JSON file and generate an explanation.
        """
        try:
            # Parse lab results from JSON file
            lab_results = self._parse_lab_results(input)
            
            # Generate prompt
            prompt = self._generate_prompt(lab_results)
            
            return prompt
            
        except Exception as e:
            return f"Error processing lab results: {str(e)}"