import subprocess
import os

voice_model = os.path.expanduser("~/.local/share/piper/voices/en_US-amy-medium.onnx")

def speak(text):
    print(f"JARVIS says: {text}")
    
    # Use Piper to generate speech
    process = subprocess.Popen(
        ["piper", "--model", voice_model, "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    
    audio_data, _ = process.communicate(input=text.encode())
    
    # Play the audio
    play_process = subprocess.Popen(
        ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
        stdin=subprocess.PIPE
    )
    play_process.communicate(input=audio_data)

# Test it
speak("Hello sir. JARVIS is now online and ready to assist you.")
speak("Would you like me to turn on the lights?")
