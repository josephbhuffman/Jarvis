from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import asyncio
import json
import psutil
import time

app = FastAPI()
llm = JarvisLLM()
mqtt = JarvisMQTT()

start_time = time.time()
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
    return HTMLResponse(open("dashboard.html").read())

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

@app.get("/stats")
async def get_stats():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    uptime_seconds = int(time.time() - start_time)
    
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime = f"{hours}h {minutes}m"
    
    return {
        "cpu": round(cpu, 1),
        "memory": round(memory, 1),
        "uptime": uptime
    }

@app.get("/health")
async def health():
    return {"status": "online", "llm": "llama3.2", "mqtt": "connected"}
























































from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import asyncio
import json
import psutil
import time

app = FastAPI()
llm = JarvisLLM()
mqtt = JarvisMQTT()

start_time = time.time()
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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #00ff00;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 48px;
            color: #00ff00;
            text-shadow: 0 0 20px #00ff00, 0 0 40px #00ff00;
            animation: glow 2s ease-in-out infinite alternate;
            margin-bottom: 10px;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00; }
            to { text-shadow: 0 0 20px #00ff00, 0 0 40px #00ff00, 0 0 60px #00ff00; }
        }
        
        .status-bar {
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(0, 255, 0, 0.05);
            border: 1px solid #00ff00;
            border-radius: 10px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.7;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }
        
        .main-panel {
            display: grid;
            grid-template-columns: 3fr 1fr;
            gap: 20px;
        }
        
        #chat {
            height: 500px;
            overflow-y: auto;
            border: 2px solid #00ff00;
            padding: 20px;
            background: rgba(0, 0, 0, 0.8);
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.3), inset 0 0 20px rgba(0, 255, 0, 0.1);
            border-radius: 10px;
        }
        
        #chat::-webkit-scrollbar {
            width: 10px;
        }
        
        #chat::-webkit-scrollbar-track {
            background: #000;
        }
        
        #chat::-webkit-scrollbar-thumb {
            background: #00ff00;
            border-radius: 5px;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 10px;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .user {
            background: rgba(0, 100, 255, 0.3);
            border-left: 4px solid #0066ff;
            text-align: right;
        }
        
        .jarvis {
            background: rgba(0, 255, 0, 0.2);
            border-left: 4px solid #00ff00;
        }
        
        .typing {
            opacity: 0.7;
            font-style: italic;
        }
        
        .typing::after {
            content: '...';
            animation: dots 1.5s infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .panel {
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff00;
            border-radius: 10px;
            padding: 15px;
        }
        
        .panel h3 {
            margin-bottom: 15px;
            font-size: 18px;
            color: #00ff00;
        }
        
        .quick-action {
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 12px;
            margin: 5px 0;
            cursor: pointer;
            border-radius: 5px;
            transition: all 0.3s;
            text-align: center;
        }
        
        .quick-action:hover {
            background: rgba(0, 255, 0, 0.3);
            box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
            transform: translateX(5px);
        }
        
        #input-area {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        input {
            flex: 1;
            padding: 15px;
            font-size: 16px;
            background: rgba(0, 0, 0, 0.9);
            border: 2px solid #00ff00;
            color: #00ff00;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        }
        
        input:focus {
            outline: none;
            box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
        }
        
        button {
            padding: 15px 30px;
            font-size: 16px;
            background: #00ff00;
            border: none;
            color: #000;
            cursor: pointer;
            font-weight: bold;
            border-radius: 5px;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
        }
        
        button:hover {
            background: #00cc00;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.8);
            transform: scale(1.05);
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-online {
            background: #00ff00;
            box-shadow: 0 0 10px #00ff00;
            animation: pulse 2s infinite;
        }
        
        .status-offline {
            background: #ff0000;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .system-info {
            font-size: 12px;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .main-panel {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 J.A.R.V.I.S.</h1>
            <div style="font-size: 14px; opacity: 0.7;">Just A Rather Very Intelligent System</div>
        </header>
        
        <div class="status-bar">
            <div class="stat">
                <div class="stat-label">STATUS</div>
                <div class="stat-value">
                    <span class="status-indicator" id="status-dot"></span>
                    <span id="status-text">OFFLINE</span>
                </div>
            </div>
            <div class="stat">
                <div class="stat-label">CPU</div>
                <div class="stat-value" id="cpu">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">MEMORY</div>
                <div class="stat-value" id="memory">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">UPTIME</div>
                <div class="stat-value" id="uptime">--</div>
            </div>
        </div>
        
        <div class="main-panel">
            <div>
                <div id="chat"></div>
                <div id="input-area">
                    <input type="text" id="message" placeholder="Command JARVIS..." />
                    <button onclick="sendMessage()">EXECUTE</button>
                </div>
            </div>
            
            <div class="sidebar">
                <div class="panel">
                    <h3>⚡ QUICK ACTIONS</h3>
                    <div class="quick-action" onclick="quickCommand('Turn on all lights')">💡 All Lights On</div>
                    <div class="quick-action" onclick="quickCommand('Turn off all lights')">🌑 All Lights Off</div>
                    <div class="quick-action" onclick="quickCommand('What is the temperature?')">🌡️ Temperature</div>
                    <div class="quick-action" onclick="quickCommand('Good morning')">🌅 Morning Routine</div>
                    <div class="quick-action" onclick="quickCommand('Goodnight')">🌙 Night Routine</div>
                </div>
                
                <div class="panel">
                    <h3>📋 SUGGESTIONS</h3>
                    <div class="system-info">
                        • "Turn on bedroom lights"<br>
                        • "What's the status?"<br>
                        • "Set temperature to 72"<br>
                        • "Is anyone home?"<br>
                        • "Start movie mode"
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket("ws://localhost:8000/ws");
        const chat = document.getElementById('chat');
        const status = document.getElementById('status-text');
        const statusDot = document.getElementById('status-dot');
        const input = document.getElementById('message');
        
        ws.onopen = () => {
            status.textContent = 'ONLINE';
            statusDot.className = 'status-indicator status-online';
            addSystemMessage('🟢 JARVIS systems online');
        };
        
        ws.onclose = () => {
            status.textContent = 'OFFLINE';
            statusDot.className = 'status-indicator status-offline';
            addSystemMessage('🔴 Connection lost');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'response') {
                removeTyping();
                addMessage('JARVIS: ' + data.message, 'jarvis');
            } else if (data.type === 'stats') {
                updateStats(data);
            }
        };
        
        function updateStats(data) {
            document.getElementById('cpu').textContent = data.cpu + '%';
            document.getElementById('memory').textContent = data.memory + '%';
            document.getElementById('uptime').textContent = data.uptime;
        }
        
        function addMessage(text, type) {
            const msg = document.createElement('div');
            msg.className = 'message ' + type;
            msg.textContent = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function addSystemMessage(text) {
            const msg = document.createElement('div');
            msg.style.cssText = 'text-align: center; opacity: 0.5; margin: 10px 0; font-size: 12px;';
            msg.textContent = text;
            chat.appendChild(msg);
        }
        
        function addTyping() {
            const typing = document.createElement('div');
            typing.className = 'message jarvis typing';
            typing.id = 'typing-indicator';
            typing.textContent = 'JARVIS is thinking';
            chat.appendChild(typing);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function removeTyping() {
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
        }
        
        function sendMessage() {
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('You: ' + message, 'user');
            addTyping();
            ws.send(JSON.stringify({message: message}));
            input.value = '';
        }
        
        function quickCommand(cmd) {
            input.value = cmd;
            sendMessage();
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Request stats every 2 seconds
        setInterval(() => {
            fetch('/stats').then(r => r.json()).then(updateStats);
        }, 2000);
        
        // Initial stats load
        fetch('/stats').then(r => r.json()).then(updateStats);
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

@app.get("/stats")
async def get_stats():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    uptime_seconds = int(time.time() - start_time)
    
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime = f"{hours}h {minutes}m"
    
    return {
        "cpu": round(cpu, 1),
        "memory": round(memory, 1),
        "uptime": uptime
    }

@app.get("/health")
async def health():
    return {"status": "online", "llm": "llama3.2", "mqtt": "connected"}






























































