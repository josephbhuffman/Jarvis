import sounddevice as sd
import whisper
import numpy as np
from mqtt_client import JarvisMQTT

print("Loading Whisper model (this takes a minute)...")
model = whisper.load_model("small")
print("✅ Whisper loaded!\n")

mqtt = JarvisMQTT()
mqtt.connect()

print("🎤 JARVIS Voice Control Ready!")
print("Press ENTER to speak, or type 'quit' to exit\n")

while True:
    user_input = input("Press ENTER to speak (or 'quit'): ")
    
    if user_input.lower() == 'quit':
        break
    
    print("\n🎤 Listening... (speak now for 5 seconds)")
    
    # Record 5 seconds
    duration = 5
    sample_rate = 16000
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    
    print("🧠 Processing...")
    
    # Transcribe
    audio_data = recording.flatten()
    result = model.transcribe(audio_data, fp16=False)
    command = result['text']
    
    print(f"You said: {command}")
    
    # Send to JARVIS via MQTT
    mqtt.publish("jarvis/command", command)
    print("✅ Command sent to JARVIS!\n")

print("\n👋 Voice control stopped")
