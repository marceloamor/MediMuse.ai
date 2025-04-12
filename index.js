console.log("Welcome to MediMuse!");

document.getElementById('import-button').addEventListener('click', function() {
    const importText = document.getElementById('import-text').value;
    console.log('Imported text:', importText);
    // You can add your logic here to process the imported text
});

document.getElementById('send-button').addEventListener('click', function() {
    const chatInput = document.getElementById('chat-input').value;
    console.log('Sent message:', chatInput);
    // You can add your logic here to send the chat message
    document.getElementById('chat-input').value = ''; // Clear the input
});

document.getElementById('login-button').addEventListener('click', function() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Basic authentication - replace with your actual logic
    if (username === 'user' && password === 'password') {
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('lab-results-section').style.display = 'block';
    } else {
        alert('Login failed. Please check your username and password.');
    }
});

fetch('src/data/patient_data.json')
    .then(response => response.json())
    .then(data => {
        const labResultsContainer = document.getElementById('lab-results-container');
        if (!labResultsContainer) {
            console.error('Lab results container not found in index.html');
            return;
        }

        // Clear any existing content
        labResultsContainer.innerHTML = '';

        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                const value = data[key];

                const resultContainer = document.createElement('div');
                resultContainer.id = key;

                const label = document.createElement('label');
                label.textContent = key + ": ";
                resultContainer.appendChild(label);

                const valueElement = document.createElement('p');
                valueElement.textContent = value;
                resultContainer.appendChild(valueElement);

                labResultsContainer.appendChild(resultContainer);
            }
        }
    })
    .catch(error => console.error('Error fetching patient data:', error));

fetch('src/data/patient_data.json')
    .then(response => response.json())
    .then(data => {
        const labResultsContainer = document.getElementById('lab-results-container');
        if (!labResultsContainer) {
            console.error('Lab results container not found in index.html');
            return;
        }

        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                const value = data[key];

                const resultContainer = document.createElement('div');
                resultContainer.id = key;

                const label = document.createElement('label');
                label.textContent = key + ": ";
                resultContainer.appendChild(label);

                const valueElement = document.createElement('p');
                valueElement.textContent = value;
                resultContainer.appendChild(valueElement);

                labResultsContainer.appendChild(resultContainer);
            }
        }
    })
    .catch(error => console.error('Error fetching patient data:', error));