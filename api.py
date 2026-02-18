from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import asyncio
import json

app = FastAPI()
llm = JarvisLLM()
mqtt = JarvisMQTT()

clients = []

def handle_mqtt_response(topic, payload):
    asyncio.create_task(broadcast({"type": "response", "message": payload}))

mqtt.connect()
mqtt.subscribe("jarvis/response", handle_mqtt_response)

async def broadcast(message):
    for client in clients:
        try:
            await client.send_json(message)
        except:
            clients.remove(client)

@app.get("/")
async def get():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS Control Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #0a0a0a;
            color: #00ff00;
        }
        h1 {
            text-align: center;
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }
        #chat {
            height: 400px;
            overflow-y: auto;
            border: 2px solid #00ff00;
            padding: 20px;
            margin: 20px 0;
            background: #000;
            box-shadow: 0 0 20px rgba(0,255,0,0.3);
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .user {
            background: rgba(0,100,255,0.2);
            text-align: right;
        }
        .jarvis {
            background: rgba(0,255,0,0.2);
        }
        #input-area {
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 15px;
            font-size: 16px;
            background: #000;
            border: 2px solid #00ff00;
            color: #00ff00;
        }
        button {
            padding: 15px 30px;
            font-size: 16px;
            background: #00ff00;
            border: none;
            color: #000;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background: #00cc00;
        }
        .status {
            text-align: center;
            margin: 10px 0;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>🤖 JARVIS Control Panel</h1>
    <div class="status" id="status">Connecting...</div>
    <div id="chat"></div>
    <div id="input-area">
        <input type="text" id="message" placeholder="Talk to JARVIS..." />
        <button onclick="sendMessage()">Send</button>
    </div>
    
    <script>
        const ws = new WebSocket("ws://localhost:8000/ws");
        const chat = document.getElementById('chat');
        const status = document.getElementById('status');
        const input = document.getElementById('message');
        
        ws.onopen = () => {
            status.textContent = '✅ Connected to JARVIS';
            status.style.color = '#00ff00';
        };
        
        ws.onclose = () => {
            status.textContent = '❌ Disconnected';
            status.style.color = '#ff0000';
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'response') {
                addMessage('JARVIS: ' + data.message, 'jarvis');
            }
        };
        
        function addMessage(text, type) {
            const msg = document.createElement('div');
            msg.className = 'message ' + type;
            msg.textContent = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function sendMessage() {
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('You: ' + message, 'user');
            ws.send(JSON.stringify({message: message}));
            input.value = '';
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            user_message = message['message']
            mqtt.publish("jarvis/command", user_message)
    except:
        clients.remove(websocket)

@app.get("/health")
async def health():
    return {"status": "online", "llm": "llama3.2", "mqtt": "connected"}
