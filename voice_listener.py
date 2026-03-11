import whisper
import subprocess
import os
import numpy as np
from mqtt_client import JarvisMQTT
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceListener:
    def __init__(self, mic_device="plughw:1,0"):
        self.mic_device = mic_device
        self.mqtt = JarvisMQTT()
        
        # Load Whisper model
        logger.info("Loading Whisper model...")
        self.model = whisper.load_model("base")
        logger.info("✅ Whisper loaded")
        
        # Connect to MQTT
        self.mqtt.connect()
        
        self.running = True
    
    def record_audio(self, duration=5, filename="voice_command.wav"):
        """Record audio from mic"""
        try:
            subprocess.run([
                "arecord",
                "-D", self.mic_device,
                "-f", "cd",
                "-d", str(duration),
                "-q",  # Quiet mode
                filename
            ], check=True)
            return True
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return False
    
    def transcribe(self, audio_file):
        """Convert speech to text"""
        try:
            result = self.model.transcribe(audio_file)
            return result['text'].strip()
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def check_for_wake_word(self, duration=3):
        """Listen for wake word"""
        if not self.record_audio(duration, "wake_word.wav"):
            return False
        
        text = self.transcribe("wake_word.wav")
        
        if text:
            text_lower = text.lower()
            # Check for wake words
            wake_words = ["jarvis", "hey jarvis", "ok jarvis", "jarvis"]
            
            for wake_word in wake_words:
                if wake_word in text_lower:
                    logger.info(f"🎤 Wake word detected: {text}")
                    return True
        
        return False
    
    def listen_for_command(self, duration=5):
        """Listen for voice command after wake word"""
        logger.info("🎤 Listening for command...")
        
        if not self.record_audio(duration, "command.wav"):
            return None
        
        text = self.transcribe("command.wav")
        
        if text:
            logger.info(f"📝 Heard: {text}")
            return text
        
        return None
    
    def run(self):
        """Main listening loop"""
        logger.info("🎤 Voice listener started!")
        logger.info("Say 'Hey JARVIS' to activate...")
        
        while self.running:
            try:
                # Listen for wake word
                if self.check_for_wake_word(duration=3):
                    # Wake word detected! Listen for command
                    command = self.listen_for_command(duration=5)
                    
                    if command:
                        # Send command to JARVIS
                        self.mqtt.publish("jarvis/command", command)
                        logger.info(f"✅ Sent to JARVIS: {command}")
                    else:
                        logger.info("❌ No command heard")
                
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("👋 Stopping voice listener...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in voice loop: {e}")
                time.sleep(1)

# Run
if __name__ == "__main__":
    listener = VoiceListener()
    listener.run()
