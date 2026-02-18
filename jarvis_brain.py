from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
import time

llm = JarvisLLM()
mqtt = JarvisMQTT()

def handle_command(topic, payload):
    """When someone sends a command to JARVIS"""
    command = payload
    
    print(f"\n🎤 Command received: {command}")
    
    # Use LLM to understand the command
    intent = llm.parse_intent(command)
    
    print(f"🧠 Intent: {intent}")
    
    # Execute the action
    action = intent.get('action')
    device = intent.get('device')
    room = intent.get('room', 'bedroom')
    response = intent.get('response')
    
    if action == 'turn_on' and device == 'light':
        mqtt_topic = f"jarvis/{room}/light/set"
        mqtt.publish(mqtt_topic, "ON")
        print(f"💡 Published: {mqtt_topic} = ON")
        
    elif action == 'turn_off' and device == 'light':
        mqtt_topic = f"jarvis/{room}/light/set"
        mqtt.publish(mqtt_topic, "OFF")
        print(f"🌑 Published: {mqtt_topic} = OFF")
        
    elif action == 'query':
        print(f"❓ Query requested for {device} in {room}")
    
    # Send response back
    mqtt.publish("jarvis/response", response)
    print(f"💬 JARVIS: {response}\n")

# Connect to MQTT
mqtt.connect()

# Subscribe to command topic
mqtt.subscribe("jarvis/command", handle_command)

print("\n✅ JARVIS BRAIN is online!")
print("🧠 LLM: Llama 3.2 (local)")
print("📡 MQTT: Connected")
print("\nSend commands to: jarvis/command")
print("Example: mosquitto_pub -h localhost -t jarvis/command -m 'Turn on bedroom lights'\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 JARVIS shutting down...")
