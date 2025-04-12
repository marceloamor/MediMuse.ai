## Overview
MediMuse.ai is an AI-powered health agent that serves as a long-term personal coach and counselor, providing deeply personalized health guidance based on your complete health history, habits, and goals. Built using the Portia SDK, our agent offers consistent, empathetic support across healthcare systems.

## Why MediMuse.ai?
- **Fragmented Healthcare**: Patients often struggle with inconsistent care across different healthcare providers and systems
- **Personalized Support**: Our AI agent maintains a comprehensive understanding of your health journey
- **Empathetic Guidance**: Combines the emotional intelligence of a counselor with the knowledge of a medical professional
- **24/7 Availability**: Access support whenever you need it, without scheduling constraints

## Key Features
- **Lab Results Analysis**: AI-powered interpretation of medical test results
- **Real-time Analysis**: Streams the agent's thought process during analysis
- **Interactive Interface**: Clean, modern UI for viewing results and analysis
- **Secure Data Handling**: Local processing of sensitive health information
- **Comprehensive Reporting**: Detailed breakdowns of test results and recommendations

## Technical Stack
- **Backend**: FastAPI with Portia SDK
- **Frontend**: HTML, JavaScript, Bootstrap, and Tailwind CSS
- **AI Framework**: Portia SDK with Gemini LLM integration
- **Data Processing**: JSON-based lab results handling

## Getting Started

### Prerequisites
- Python 3.12 or higher
- Node.js (for serving the frontend)
- Required API keys:
  - Google API Key (for Gemini LLM)
  - Portia API Key
  - Tavily API Key

### Environment Setup
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd MediMuse.ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   GOOGLE_API_KEY=your_google_api_key
   PORTIA_API_KEY=your_portia_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

### Running the Application

1. Start the FastAPI backend server:
   ```bash
   cd src
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. In a new terminal, start the frontend server:
   ```bash
   cd src
   node server.js
   ```

3. Access the application:
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000

### Project Structure
```
MediMuse.ai/
├── src/
│   ├── main.py              # FastAPI backend with Portia integration
│   ├── server.js            # Frontend server
│   ├── index.html           # Main frontend interface
│   ├── index.js             # Frontend JavaScript
│   ├── index.css            # Frontend styles
│   └── data/
│       └── patient_data.json # Sample patient data
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

### Using the Application
1. **Viewing Lab Results**:
   - The application automatically loads and displays lab results from `src/data/patient_data.json`
   - Results are presented in a clean, tabular format

2. **Analyzing Results**:
   - Click the "Analyze Results" button to start the AI analysis
   - Watch the agent's thought process in real-time
   - View the final analysis with interpretations and recommendations

3. **Importing New Results**:
   - Use the import section to paste new lab results
   - Results should be in JSON format matching the structure in `patient_data.json`

## Development Team
- [Team Member 1]
- [Team Member 2]
- [Team Member 3]
- [Team Member 4]
- [Team Member 5]
- [Team Member 6]
- [Team Member 7]

## Contributing
We welcome contributions! Please read our contributing guidelines before submitting pull requests.

## License
[Specify your license here]

## Contact
For questions or support, please reach out to [contact information]
