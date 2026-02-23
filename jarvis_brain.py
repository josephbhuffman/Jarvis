from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import time
import requests

# Your Govee API key
GOVEE_API_KEY = "332fe7ca-0995-436d-ad33-c837ae8af443"

llm = JarvisLLM()
mqtt = JarvisMQTT()

# Store device info
govee_device = None

def init_govee():
    global govee_device
    
    headers = {"Govee-API-Key": GOVEE_API_KEY}
    response = requests.get("https://developer-api.govee.com/v1/devices", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        devices = data.get('data', {}).get('devices', [])
        if devices:
            govee_device = devices[0]
            print(f"✅ Connected to Govee: {govee_device.get('deviceName')}")
            return True
    
    print(f"❌ Govee connection failed: {response.status_code}")
    return False

def control_light(action):
    if not govee_device:
        return False
    
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    cmd = "turn" if action == "turn_on" else "turn"
    value = "on" if action == "turn_on" else "off"
    
    payload = {
        "device": govee_device['device'],
        "model": govee_device['model'],
        "cmd": {
            "name": cmd,
            "value": value
        }
    }
    
    response = requests.put(
        "https://developer-api.govee.com/v1/devices/control",
        headers=headers,
        json=payload
    )
    
    return response.status_code == 200

def handle_command(topic, payload):
    command = payload
    
    print(f"\n🎤 Command received: {command}")
    
    # Use LLM to understand the command
    intent = llm.parse_intent(command)
    
    print(f"🧠 Intent: {intent}")
    
    # Execute the action
    action = intent.get('action')
    device = intent.get('device')
    response = intent.get('response')
    
    # Control real Govee light!
    if device == 'light':
        if action == 'turn_on':
            success = control_light('turn_on')
            if success:
                print(f"💡 REAL LIGHT TURNED ON!")
                response = "Light is now on"
            else:
                print("❌ Failed to turn on light")
                response = "Failed to turn on light"
                
        elif action == 'turn_off':
            success = control_light('turn_off')
            if success:
                print(f"🌑 REAL LIGHT TURNED OFF!")
                response = "Light is now off"
            else:
                print("❌ Failed to turn off light")
                response = "Failed to turn off light"
    
    # Send response back
    mqtt.publish("jarvis/response", response)
    print(f"💬 JARVIS: {response}\n")

# Initialize Govee
print("Initializing Govee connection...")
init_govee()

# Connect to MQTT
mqtt.connect()
mqtt.subscribe("jarvis/command", handle_command)

print("\n✅ JARVIS BRAIN is online!")
print("🧠 LLM: Llama 3.2 (local)")
print("📡 MQTT: Connected")
print("💡 Govee: Ready")
print("\nSend commands to: jarvis/command\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 JARVIS shutting down...")














