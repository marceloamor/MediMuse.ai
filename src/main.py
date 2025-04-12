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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Load API keys from environment
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PORTIA_API_KEY = os.getenv('PORTIA_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

if not all([GOOGLE_API_KEY, PORTIA_API_KEY, TAVILY_API_KEY]):
    raise ValueError("Missing required API keys in environment variables")

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/analyze-lab-results")
async def analyze_lab_results(request: Request, lab_results: dict):
    """Endpoint to analyze lab results using the Portia agent."""
    try:
        logger.info("Received request to analyze lab results")
        logger.info(f"Request body: {lab_results}")
        
        # Validate the lab results
        if not lab_results:
            logger.error("Empty lab results received")
            raise HTTPException(status_code=400, detail="Lab results data is required")
            
        # Log the request headers for debugging
        logger.info(f"Request headers: {dict(request.headers)}")
        
        return StreamingResponse(
            stream_portia_analysis(lab_results),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in analyze_lab_results endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def stream_portia_analysis(lab_results: dict):
    """Stream the Portia agent's analysis of lab results."""
    logger.info("Starting Portia analysis...")
    logger.info(f"Lab results received: {lab_results}")
    
    try:
        # Create a temporary JSON file with the lab results
        temp_file = "temp_lab_results.json"
        logger.info(f"Creating temporary file: {temp_file}")
        
        with open(temp_file, "w") as f:
            json.dump(lab_results, f)
            logger.info("Temporary file created successfully")

        # Plan the analysis
        logger.info("Planning analysis with Portia...")
        plan = portia.plan(
            f"Analyze the lab results from {temp_file} and provide a comprehensive explanation. "
            "If any of the values suggest a specific health issue, please diagnose it and suggest next steps "
            "to bring up with a professional health care provider."
        )
        logger.info(f"Plan created with {len(plan.steps)} steps")

        # Stream the plan steps
        for step in plan.steps:
            step_info = f"Planning step: {step.task}"
            logger.info(step_info)
            yield f"data: {json.dumps({'type': 'thought', 'content': step_info})}\n\n"
            await asyncio.sleep(0.1)

        # Run the plan and stream the results
        logger.info("Executing plan...")
        run = portia.run_plan(plan)
        
        if run.state == PlanRunState.COMPLETE:
            logger.info("Plan execution completed successfully")
            # Get the analysis results
            if run.outputs.step_outputs:
                # Debug logging to see all available outputs
                logger.info("Available step outputs:")
                for key, output in run.outputs.step_outputs.items():
                    logger.info(f"Key: {key}")
                    logger.info(f"Output type: {type(output)}")
                    logger.info(f"Output value: {output.value[:200]}...")  # First 200 chars
                
                # Find the output from the lab results tool that contains the LLM analysis
                analysis_found = False
                for key, output in run.outputs.step_outputs.items():
                    if key.startswith("$lab_results_tool"):
                        # Check if this output contains the LLM analysis
                        if isinstance(output.value, str) and len(output.value) > 100:  # LLM analysis should be longer
                            analysis = output.value
                            logger.info("LLM analysis found in output")
                            analysis_found = True
                            
                            # Stream the analysis in chunks
                            for chunk in analysis.split('\n'):
                                logger.info(f"Streaming chunk: {chunk[:50]}...")  # Log first 50 chars of each chunk
                                yield f"data: {json.dumps({'type': 'analysis', 'content': chunk})}\n\n"
                                await asyncio.sleep(0.1)
                            break
                
                if not analysis_found:
                    error_msg = "No LLM analysis found in the outputs"
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
            else:
                error_msg = "No analysis results found"
                logger.error(error_msg)
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        else:
            error_msg = f"Analysis failed with state: {run.state}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    except Exception as e:
        error_msg = f"Error during analysis: {str(e)}"
        logger.error(error_msg, exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            logger.info(f"Cleaning up temporary file: {temp_file}")
            os.remove(temp_file)
            logger.info("Temporary file removed")

@app.post("/chat")
async def chat(request: Request):
    """Endpoint to handle chat messages with the Portia agent."""
    try:
        logger.info("Received chat request")
        data = await request.json()
        message = data.get("message")
        lab_results = data.get("lab_results", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
            
        logger.info(f"Processing chat message: {message}")
        logger.info(f"Lab results: {lab_results}")
        
        return StreamingResponse(
            stream_portia_response(message, lab_results),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def stream_portia_response(message: str, lab_results: dict):
    """Stream the Portia agent's response to a chat message."""
    logger.info("Starting Portia response...")
    
    try:
        # Create a temporary JSON file with the lab results
        temp_file = "temp_lab_results.json"
        logger.info(f"Creating temporary file: {temp_file}")
        
        with open(temp_file, "w") as f:
            json.dump(lab_results, f)
            logger.info("Temporary file created successfully")

        # Plan the response
        logger.info("Planning response with Portia...")
        plan = portia.plan(
            f"Analyze the lab results from {temp_file} and respond to the following message: {message}. "
            "Provide a comprehensive response that takes into account the lab results and the user's question. "
            "If the message is about specific test results, focus on those tests. "
            "If it's a general health question, provide relevant information based on the lab results."
        )
        logger.info(f"Plan created with {len(plan.steps)} steps")

        # Stream the plan steps
        for step in plan.steps:
            step_info = f"Planning step: {step.task}"
            logger.info(step_info)
            yield f"data: {json.dumps({'type': 'thought', 'content': step_info})}\n\n"
            await asyncio.sleep(0.1)

        # Run the plan and stream the results
        logger.info("Executing plan...")
        run = portia.run_plan(plan)
        
        if run.state == PlanRunState.COMPLETE:
            logger.info("Plan execution completed successfully")
            # Get the response
            if run.outputs.step_outputs:
                # Debug logging to see all available outputs
                logger.info("Available step outputs:")
                for key, output in run.outputs.step_outputs.items():
                    logger.info(f"Key: {key}")
                    logger.info(f"Output type: {type(output)}")
                    logger.info(f"Output value: {output.value[:200]}...")  # First 200 chars
                
                # Find the output from the lab results tool that contains the LLM analysis
                response_found = False
                for key, output in run.outputs.step_outputs.items():
                    if key.startswith("$lab_results_tool"):
                        # Check if this output contains the LLM analysis
                        if isinstance(output.value, str) and len(output.value) > 100:  # LLM analysis should be longer
                            response = output.value
                            logger.info("LLM response found in output")
                            response_found = True
                            
                            # Stream the response in chunks
                            for chunk in response.split('\n'):
                                logger.info(f"Streaming chunk: {chunk[:50]}...")  # Log first 50 chars of each chunk
                                yield f"data: {json.dumps({'type': 'response', 'content': chunk})}\n\n"
                                await asyncio.sleep(0.1)
                            break
                
                if not response_found:
                    error_msg = "No LLM response found in the outputs"
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
            else:
                error_msg = "No response found"
                logger.error(error_msg)
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        else:
            error_msg = f"Response generation failed with state: {run.state}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

    except Exception as e:
        error_msg = f"Error during response generation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            logger.info(f"Cleaning up temporary file: {temp_file}")
            os.remove(temp_file)
            logger.info("Temporary file removed")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)