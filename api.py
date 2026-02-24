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
    with open("dashboard_v2.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(html_content)

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










