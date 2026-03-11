import whisper
import subprocess

print("Loading Whisper model...")
model = whisper.load_model("base")

print("Recording 5 seconds...")
subprocess.run([
    "arecord", "-D", "plughw:1,0", "-f", "cd", "-d", "5", "test_voice.wav"
])

print("Transcribing...")
result = model.transcribe("test_voice.wav")

print(f"\nYou said: {result['text']}")
