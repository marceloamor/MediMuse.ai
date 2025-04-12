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