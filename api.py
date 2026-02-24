from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import asyncio
import json
import psutil
import time
import requests

app = FastAPI()
llm = JarvisLLM()
mqtt = JarvisMQTT()

start_time = time.time()
clients = []

GOVEE_API_KEY = "332fe7ca-0995-436d-ad33-c837ae8af443"

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
    with open("dashboard_clean.html", "r") as f:
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

@app.post("/control/light1/on")
async def light1_on():
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "device": "14:B5:98:17:3C:F2:CE:56",
        "model": "H6008",
        "cmd": {"name": "turn", "value": "on"}
    }
    
    response = requests.put(
        "https://developer-api.govee.com/v1/devices/control",
        headers=headers,
        json=payload
    )
    
    return {"success": response.status_code == 200}

@app.post("/control/light1/off")
async def light1_off():
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "device": "14:B5:98:17:3C:F2:CE:56",
        "model": "H6008",
        "cmd": {"name": "turn", "value": "off"}
    }
    
    response = requests.put(
        "https://developer-api.govee.com/v1/devices/control",
        headers=headers,
        json=payload
    )
    
    return {"success": response.status_code == 200}

@app.post("/control/light2/on")
async def light2_on():
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "device": "1F:EF:98:17:3C:F2:61:96",
        "model": "H6008",
        "cmd": {"name": "turn", "value": "on"}
    }
    
    response = requests.put(
        "https://developer-api.govee.com/v1/devices/control",
        headers=headers,
        json=payload
    )
    
    return {"success": response.status_code == 200}

@app.post("/control/light2/off")
async def light2_off():
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "device": "1F:EF:98:17:3C:F2:61:96",
        "model": "H6008",
        "cmd": {"name": "turn", "value": "off"}
    }
    
    response = requests.put(
        "https://developer-api.govee.com/v1/devices/control",
        headers=headers,
        json=payload
    )
    
    return {"success": response.status_code == 200}

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
