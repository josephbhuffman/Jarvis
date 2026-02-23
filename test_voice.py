import sounddevice as sd
import whisper
import numpy as np

print("Loading Whisper model...")
model = whisper.load_model("small")
print("Whisper loaded!")

print("\nRecording 5 seconds... SPEAK NOW!")

# Record 5 seconds of audio
duration = 5
sample_rate = 16000
recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
sd.wait()

print("Recording complete! Processing...")

# Convert to format Whisper expects
audio_data = recording.flatten()

# Transcribe
result = model.transcribe(audio_data, fp16=False)

print(f"\nYou said: {result['text']}")
