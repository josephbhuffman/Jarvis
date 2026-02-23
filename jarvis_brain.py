from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import time
import requests
import subprocess
import os

# Your Govee API key
GOVEE_API_KEY = "332fe7ca-0995-436d-ad33-c837ae8af443"

llm = JarvisLLM()
mqtt = JarvisMQTT()

voice_model = os.path.expanduser("~/.local/share/piper/voices/en_US-amy-medium.onnx")

def speak(text):
    """Make JARVIS speak out loud"""
    print(f"🔊 Speaking: {text}")
    
    process = subprocess.Popen(
        ["piper", "--model", voice_model, "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    audio_data, _ = process.communicate(input=text.encode())
    
    play_process = subprocess.Popen(
        ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
        stdin=subprocess.PIPE
    )
    play_process.communicate(input=audio_data)

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
    
    cmd = "turn"
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
    
    # Try to parse as home automation command
    try:
        intent = llm.parse_intent(command)
        print(f"🧠 Intent: {intent}")
    except Exception as e:
        print(f"⚠️ Intent parsing error: {e}")
        intent = None
    
    response = None
    
    # Check if we got a valid intent for device control
    if intent and isinstance(intent, dict):
        action = intent.get('action')
        device = intent.get('device')
        
        # Device control commands
        if device == 'light' and action in ['turn_on', 'turn_off']:
            if action == 'turn_on':
                success = control_light('turn_on')
                if success:
                    print(f"💡 REAL LIGHT TURNED ON!")
                    response = "Light is now on"
                else:
                    response = "Failed to turn on light"
                    
            elif action == 'turn_off':
                success = control_light('turn_off')
                if success:
                    print(f"🌑 REAL LIGHT TURNED OFF!")
                    response = "Light is now off"
                else:
                    response = "Failed to turn off light"
    
    # If no device command or intent failed, have conversation
    if not response:
        print(f"💬 Having conversation...")
        try:
            response = llm.conversation(command)
        except Exception as e:
            print(f"⚠️ Conversation error: {e}")
            response = "I'm having trouble processing that request right now."
    
    # Send response back
    mqtt.publish("jarvis/response", response)
    print(f"💬 JARVIS: {response}\n")
    speak(response)

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
print("\nReady for commands!\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 JARVIS shutting down...")






