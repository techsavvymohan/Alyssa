from flask import Flask, render_template_string, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import logging
from flask_caching import Cache
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['GROQ_API_KEY'] = os.environ.get("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=app.config['GROQ_API_KEY'])

# Initialize caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chat page template with code highlighting and copy functionality
chat_page = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alyssa AI Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@600&display=swap" rel="stylesheet">
    <style>
        body { background-color: #1f1c2c; color: white; font-family: 'Arial', monospace; }
        .container { max-width: 800px; margin: 50px auto; background-color: #2c2c54; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3); }
        .chat-box { max-height: 500px; overflow-y: auto; margin-bottom: 20px; background-color: #444; padding: 15px; border-radius: 8px; color: #e0e0e0; }
        .input-box { width: 100%; background-color: #333; border: 2px solid #e0e0e0; border-radius: 20px; padding: 15px; font-size: 1rem; color: #f9f9f9; margin-bottom: 15px; resize: none; }
        .btn-send { position: absolute; right: 10px; bottom: 10px; background-color: #00d1b2; color: white; border: none; padding: 10px; border-radius: 50%; cursor: pointer; height: 40px; width: 40px; }
        .message { margin: 5px 0; padding: 10px; border-radius: 15px; max-width: 80%; }
        .user-message { background-color: #008c7a; color: white; margin-left: auto; border-top-left-radius: 0; }
        .ai-message { background-color: #2a2a72; color: white; }
        .btn-toggle { background-color: transparent; border: none; color: white; cursor: pointer; position: absolute; top: 10px; right: 10px; font-size: 1.5rem; }
        .app-name { font-size: 2.5rem; font-weight: 600; text-align: center; color: #00d1b2; text-shadow: 4px 4px 10px rgba(0, 0, 0, 0.5); border: 2px solid #00d1b2; padding: 10px; border-radius: 8px; }
        .light-mode body { background-color: #f0f0f0; color: #333; }
        .light-mode .container { background-color: #ffffff; }
        .light-mode .chat-box { background-color: #e0e0e0; color: #333; }
        .light-mode .input-box { background-color: #ffffff; color: #333; }
        .light-mode .user-message { background-color: #a8e6cf; color: #333; }
        .light-mode .ai-message { background-color: #d5b8f7; color: #333; }
        @media (max-width: 600px) {
            .app-name { font-size: 1.8rem; }
            .btn-toggle { font-size: 1.2rem; }
            .input-box { padding: 10px; }
            .btn-send { height: 35px; width: 35px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="app-name">Alyssa</h1>
        <button class="btn-toggle" onclick="toggleMode()" id="modeButton"><i class="fas fa-moon" id="modeIcon"></i></button>
        <div class="chat-box" id="chat-box"></div>
        <div class="input-group">
            <textarea id="user_input" class="input-box" placeholder="Ask me anything..."></textarea>
            <button class="btn-send" onclick="sendMessage()"><i class="fas fa-paper-plane"></i></button>
        </div>
    </div>

    <script>
        let isDarkMode = true;
        function toggleMode() {
            isDarkMode = !isDarkMode;
            document.body.classList.toggle('light-mode', !isDarkMode);
            document.getElementById('modeIcon').classList.toggle('fa-sun', !isDarkMode);
            document.getElementById('modeIcon').classList.toggle('fa-moon', isDarkMode);
        }
        
        function sendMessage() {
            const userInput = document.getElementById('user_input').value;
            if (!userInput.trim()) { alert('Please enter a message.'); return; }
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += `<div class="message user-message"><i class="fas fa-user" style="color: #fff;"></i> <span>${userInput}</span></div>`;
            document.getElementById('user_input').value = '';
            fetch('/chat', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'message=' + encodeURIComponent(userInput) })
            .then(response => response.json()).then(data => {
                if (data.error) {
                    chatBox.innerHTML += `<div class="message ai-message">Error: ${data.error}</div>`;
                } else {
                    chatBox.innerHTML += `<div class="message ai-message"><i class="fas fa-robot" style="color: #00d1b2;"></i> <span>${data.response}</span></div>`;
                    if (data.is_code) {
                        chatBox.innerHTML += "<button id='copyButton' onclick='copyCode()'>Copy Code</button>";
                    }
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }).catch(console.error);
        }

        function copyCode() {
            const codeBlock = document.querySelector('pre code').innerText;
            navigator.clipboard.writeText(codeBlock).then(() => {
                alert("Code copied to clipboard!");
            }).catch(err => {
                console.error('Failed to copy code: ', err);
            });
        }

        document.getElementById('user_input').addEventListener('keypress', e => { if (e.key === 'Enter') { e.preventDefault(); sendMessage(); } });
    </script>
</body>
</html>
'''

@app.route('/')
def chat():
    """Renders the chat page."""
    try:
        return render_template_string(chat_page)
    except Exception as e:
        logger.error(f"Error rendering chat page: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat_response():
    """Handles chat responses."""
    user_message = request.form['message']
    
    # Input validation
    if not user_message.strip():
        return jsonify({'error': 'Please enter a valid message.'})
    
    try:
        # Check if the user's message is a greeting
        if "hello" in user_message.lower() or "hi" in user_message.lower():
            response_text = "Hey, my name is Alyssa. How can I assist you today?"
            is_code = False
        else:
            # Cache chat completion results
            cache_key = f"chat_completion_{user_message}"
            response_text = cache.get(cache_key)
            
            if response_text is None:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": "You are a helpful AI assistant."}, 
                              {"role": "user", "content": user_message}],
                    model="llama3-8b-8192"  # Use your chosen model here
                )
                response_text = chat_completion.choices[0].message.content
                cache.set(cache_key, response_text)

            # Check if the response contains code (simplistic check)
            is_code = response_text.strip().startswith("```")

        return jsonify({'response': response_text, 'is_code': is_code})

    except Exception as e:
        logger.error(f"Error processing chat response: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request.'})

if __name__ == '__main__':
    app.run(debug=True)
