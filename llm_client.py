import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisLLM:
    def __init__(self, model="llama3.2", host="http://localhost:11434"):
        self.model = model
        self.host = host
        self.context = []
        
    def chat(self, message, system_prompt=None):
        """Send message to LLM and get response"""
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": message
        })
        
        logger.info(f"Sending to LLM: {message}")
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )
            
            result = response.json()
            reply = result["message"]["content"]
            
            logger.info(f"LLM response: {reply}")
            return reply
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "I'm having trouble thinking right now."
    
    def parse_intent(self, message):
        """Use LLM to parse user intent for home automation"""
        
        system_prompt = """You are JARVIS, a home automation assistant.
Parse user commands and respond with JSON containing:
- action: what to do (turn_on, turn_off, query, etc)
- device: what device (light, plug, sensor, etc)
- room: which room (bedroom, kitchen, etc)
- response: friendly response to user

Examples:
User: "Turn on bedroom lights"
{"action": "turn_on", "device": "light", "room": "bedroom", "response": "Turning on bedroom lights"}

User: "What's the temperature?"
{"action": "query", "device": "temperature", "room": "bedroom", "response": "Checking bedroom temperature"}

Only respond with valid JSON, nothing else."""

        response = self.chat(message, system_prompt)
        
        try:
            intent = json.loads(response)
            return intent
        except:
            return {
                "action": "unknown",
                "response": response
            }
