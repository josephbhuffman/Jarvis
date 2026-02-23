import sounddevice as sd
import numpy as np
from openwakeword.model import Model
import time

print("Loading wake word model...")
model = Model()

print("\nAvailable wake words:")
for word in model.models.keys():
    print(f"  - {word}")

print("\n🎤 Listening... Say any wake word above")
print("Press Ctrl+C to stop\n")

sample_rate = 16000
chunk_size = 1280

with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
    while True:
        audio_chunk, _ = stream.read(chunk_size)
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        
        # Get predictions
        prediction = model.predict(audio_array)
        
        # Check each model
        for wake_word, score in prediction.items():
            if wake_word == "hey_jarvis" and score > 0.1:
                print(f"🔊 JARVIS DETECTED! Score: {score:.2f}")
        
        time.sleep(0.01)
