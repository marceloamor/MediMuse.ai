console.log("Welcome to MediMuse!");

// Function to display lab results
function displayLabResults(data) {
    const labResultsContainer = document.getElementById('lab-results-container');
    if (!labResultsContainer) {
        console.error('Lab results container not found in index.html');
        return;
    }

    // Clear any existing content
    labResultsContainer.innerHTML = '';

    // Add each test result to the table
    for (const [testName, value] of Object.entries(data)) {
        // Skip patient information
        if (['PatientName', 'PatientSex', 'PatientAge', 'PatientWeight'].includes(testName)) {
            continue;
        }

        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';

        // Test Name
        const nameCell = document.createElement('td');
        nameCell.className = 'px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900';
        nameCell.textContent = testName;
        row.appendChild(nameCell);

        // Value
        const valueCell = document.createElement('td');
        valueCell.className = 'px-6 py-4 whitespace-nowrap text-sm text-gray-500';
        valueCell.textContent = value;
        row.appendChild(valueCell);

        labResultsContainer.appendChild(row);
    }
}

// Function to display analysis results
function displayAnalysis(analysis) {
    const analysisContainer = document.getElementById('analysis-container');
    if (!analysisContainer) {
        console.error('Analysis container not found in index.html');
        return;
    }

    // Clear any existing content
    analysisContainer.innerHTML = '';

    // Create sections for different parts of the analysis
    const sections = {
        'Overview': analysis.overview || '',
        'Test Analysis': analysis.test_analysis || [],
        'Recommendations': analysis.recommendations || [],
        'Follow-up Actions': analysis.follow_up_actions || []
    };

    // Create and append each section
    for (const [title, content] of Object.entries(sections)) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'mb-6';

        const sectionTitle = document.createElement('h3');
        sectionTitle.className = 'text-lg font-semibold mb-2 text-blue-600';
        sectionTitle.textContent = title;
        sectionDiv.appendChild(sectionTitle);

        if (Array.isArray(content)) {
            const list = document.createElement('ul');
            list.className = 'list-disc pl-5 space-y-1';
            content.forEach(item => {
                const listItem = document.createElement('li');
                listItem.className = 'text-gray-700';
                listItem.textContent = item;
                list.appendChild(listItem);
            });
            sectionDiv.appendChild(list);
        } else {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'text-gray-700';
            contentDiv.textContent = content;
            sectionDiv.appendChild(contentDiv);
        }

        analysisContainer.appendChild(sectionDiv);
    }
}

// Function to add a message to the chat
function addMessage(content, isUser = false) {
    const chatFrame = document.getElementById('chat-frame');
    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-2 p-2 rounded-lg ${isUser ? 'bg-blue-100 ml-auto' : 'bg-gray-100'}`;
    messageDiv.style.maxWidth = '80%';
    messageDiv.style.marginLeft = isUser ? 'auto' : '0';
    messageDiv.textContent = content;
    chatFrame.appendChild(messageDiv);
    chatFrame.scrollTop = chatFrame.scrollHeight;
}

// Function to handle chat messages
async function handleChatMessage(message) {
    try {
        // Get current lab results
        const labResults = {};
        const rows = document.querySelectorAll('#lab-results-container tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 2) {
                labResults[cells[0].textContent] = cells[1].textContent;
            }
        });

        // Add user message to chat
        addMessage(message, true);

        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'mb-2 p-2 bg-gray-100 rounded-lg';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.textContent = 'MediMuse is thinking...';
        document.getElementById('chat-frame').appendChild(loadingDiv);

        // Send message to backend
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                lab_results: labResults
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let responseContent = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'thought') {
                            // Update loading indicator with thought
                            document.getElementById('loading-indicator').textContent = data.content;
                        } else if (data.type === 'response') {
                            // Remove loading indicator if it's the first response chunk
                            if (responseContent === '') {
                                document.getElementById('loading-indicator').remove();
                            }
                            // Add response content
                            responseContent += data.content + '\n';
                            addMessage(responseContent.trim());
                        } else if (data.type === 'error') {
                            // Remove loading indicator and show error
                            document.getElementById('loading-indicator').remove();
                            addMessage(`Error: ${data.content}`);
                        }
                    } catch (e) {
                        console.error('Error parsing message:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your message. Please try again.');
    }
}

// Function to fetch and display patient data
async function fetchPatientData() {
    try {
        const response = await fetch('/patient-data');
        if (!response.ok) {
            throw new Error('Failed to fetch patient data');
        }
        const data = await response.json();
        displayLabResults(data);
    } catch (error) {
        console.error('Error fetching patient data:', error);
    }
}

// Utility function to log to both console and UI
function logToUI(message, type = 'info') {
    // Log to browser console
    console.log(message);
    
    // Log to UI console
    const consoleContent = document.getElementById('console-content');
    if (consoleContent) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `mb-1 ${type === 'error' ? 'text-red-500' : 'text-green-500'}`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        consoleContent.appendChild(logEntry);
        consoleContent.scrollTop = consoleContent.scrollHeight;
    }
}

// Function to analyze lab results using Portia agent
async function analyzeLabResults(data) {
    try {
        // Show loading state
        const analysisContainer = document.getElementById('analysis-container');
        const streamingContent = document.getElementById('streaming-content');
        analysisContainer.innerHTML = '<div class="text-center py-4">Analysis in progress...</div>';
        streamingContent.innerHTML = '';
        
        const response = await fetch('http://localhost:8000/analyze-lab-results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let analysisChunks = [];

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'thought') {
                            // Add thought to streaming content with a nice format
                            streamingContent.innerHTML += `
                                <div class="mb-2 p-2 bg-blue-50 rounded-lg">
                                    <div class="flex items-center text-blue-600 mb-1">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                                        </svg>
                                        <span class="font-medium">Agent's Thought</span>
                                    </div>
                                    <div class="text-gray-700">${data.content}</div>
                                </div>
                            `;
                        } else if (data.type === 'analysis') {
                            // Accumulate analysis chunks
                            if (data.content && typeof data.content === 'string') {
                                analysisChunks.push(data.content);
                            }
                        } else if (data.type === 'error') {
                            streamingContent.innerHTML += `
                                <div class="mb-2 p-2 bg-red-50 rounded-lg">
                                    <div class="flex items-center text-red-600 mb-1">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <span class="font-medium">Error</span>
                                    </div>
                                    <div class="text-gray-700">${data.content}</div>
                                </div>
                            `;
                        }
                        streamingContent.scrollTop = streamingContent.scrollHeight;
                    } catch (e) {
                        console.error('Error parsing message:', e);
                    }
                }
            }
        }

        // After all chunks are received, display the complete analysis
        if (analysisChunks.length > 0) {
            const completeAnalysis = analysisChunks.join('\n');
            analysisContainer.innerHTML = `
                <div class="prose max-w-none">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Analysis Summary</h3>
                    <div class="text-gray-700 whitespace-pre-wrap">${completeAnalysis}</div>
                </div>
            `;
        }
    } catch (error) {
        const errorMessage = 'Error: Could not analyze lab results. Please try again later.';
        streamingContent.innerHTML += `
            <div class="mb-2 p-2 bg-red-50 rounded-lg">
                <div class="flex items-center text-red-600 mb-1">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span class="font-medium">Error</span>
                </div>
                <div class="text-gray-700">${errorMessage}</div>
            </div>
        `;
        analysisContainer.innerHTML = `<div class="text-center py-4 text-red-600">${errorMessage}</div>`;
    }
}

// Event Listeners
document.getElementById('import-button').addEventListener('click', function() {
    const importText = document.getElementById('import-results').value;
    try {
        const labResults = JSON.parse(importText);
        displayLabResults(labResults);
    } catch (e) {
        console.error('Error parsing imported results:', e);
        alert('Invalid JSON format. Please check your input.');
    }
});

document.getElementById('send-button').addEventListener('click', function() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    if (message === '') return;

    handleChatMessage(message);
    chatInput.value = '';
});

document.getElementById('login-button').addEventListener('click', function() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Basic authentication - replace with your actual logic
    if (username === 'user' && password === 'password') {
        // Hide login container
        document.getElementById('login-container').style.display = 'none';
        // Show main content
        document.getElementById('main-content').style.display = 'block';
        // Fetch and display patient data after login
        fetchPatientData();
    } else {
        alert('Login failed. Please check your username and password.');
    }
});

// Add event listener for analyze button
document.getElementById('analyze-button').addEventListener('click', function() {
    // Show analysis section
    document.getElementById('analysis-section').style.display = 'block';
    // Get the current lab results data
    const labResults = {};
    const rows = document.querySelectorAll('#lab-results-container tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length === 2) {
            labResults[cells[0].textContent] = cells[1].textContent;
        }
    });
    // Start analysis
    analyzeLabResults(labResults);
});

// Initialize
console.log("Fetching patient data...");
fetchPatientData();