import sounddevice as sd
import numpy as np
import whisper
from openwakeword.model import Model
from mqtt_client import JarvisMQTT
import time

print("Loading models...")
# Load wake word detector
oww_model = Model()

# Load Whisper for commands
whisper_model = whisper.load_model("small")

mqtt = JarvisMQTT()
mqtt.connect()

print("\n✅ JARVIS Wake Word Detection Online!")
print("🎤 Listening for 'Hey JARVIS'...\n")

# Audio stream settings
sample_rate = 16000
chunk_size = 1280  # 80ms chunks

def process_audio_chunk(audio_chunk):
    """Check if wake word detected"""
    prediction = oww_model.predict(audio_chunk)
    
    for mdl in oww_model.prediction_buffer.keys():
        scores = list(oww_model.prediction_buffer[mdl])
        if scores[-1] > 0.1:  # Detection threshold
            return True
    return False

def record_command(duration=5):
    """Record audio command after wake word"""
    print("🎤 Listening for command...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return recording.flatten()

# Main listening loop
with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
    while True:
        # Read audio chunk
        audio_chunk, _ = stream.read(chunk_size)
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        
        # Check for wake word
        if process_audio_chunk(audio_array):
            print("\n🟢 Wake word detected!")
            
            # Record command
            command_audio = record_command(duration=5)
            
            # Transcribe with Whisper
            print("🧠 Processing...")
            result = whisper_model.transcribe(command_audio, fp16=False)
            command = result['text']
            
            print(f"You said: {command}")
            
            # Send to JARVIS
            mqtt.publish("jarvis/command", command)
            print("✅ Command sent!\n")
            
            # Brief pause before listening again
            time.sleep(1)
            print("🎤 Listening for 'Hey JARVIS'...\n")
