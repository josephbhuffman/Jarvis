import whisper

model = whisper.load_model("base")
print("Whisper loaded! Testing with audio file...")

# We'll test with a file first, then live mic later
