import json
import os
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from portia.tools import Tool

class ExplainLabResults(Tool):
    name = "explain_lab_result"
    description = "Explains blood test or lab result in plain language and its significance."

    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _parse_lab_results(self, json_file_path: str) -> Dict[str, Any]:
        """
        Parse lab results from JSON file.
        
        Args:
            json_file_path: Path to the JSON file containing lab results
            
        Returns:
            Dictionary containing parsed lab results
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
        
        Args:
            lab_results: Dictionary containing lab results
            
        Returns:
            Formatted prompt string
        """
        # Extract relevant information from lab results
        patient_info = lab_results.get('patient_info', {})
        tests = lab_results.get('tests', [])
        
        # Build prompt
        prompt = f"""
        Please explain the following lab results in plain language:
        
        Patient Information:
        - Name: {patient_info.get('name', 'Not provided')}
        - Age: {patient_info.get('age', 'Not provided')}
        - Gender: {patient_info.get('gender', 'Not provided')}
        
        Lab Results:
        """
        
        for test in tests:
            prompt += f"""
        - Test: {test.get('name', 'Unknown')}
          Result: {test.get('result', 'Not available')}
          Reference Range: {test.get('reference_range', 'Not available')}
          Units: {test.get('units', 'Not available')}
            """
        
        prompt += """
        Please explain:
        1. What these results mean in simple terms
        2. Whether any values are outside normal ranges
        3. What might cause any abnormal values
        4. Any recommended follow-up actions
        """
        
        return prompt

    def call(self, input: str) -> str:
        """
        Process lab results from a JSON file and generate an explanation.
        
        Args:
            input: Path to the JSON file containing lab results
            
        Returns:
            Explanation of the lab results
        """
        try:
            # Parse lab results from JSON file
            lab_results = self._parse_lab_results(input)
            
            # Generate prompt
            prompt = self._generate_prompt(lab_results)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"Error processing lab results: {str(e)}"