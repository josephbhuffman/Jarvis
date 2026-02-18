from llm_client import JarvisLLM

llm = JarvisLLM()

print("Testing JARVIS LLM...\n")

# Test 1: Simple chat
print("=== Test 1: Simple Chat ===")
response = llm.chat("Hello, I am your creator Joseph")
print(f"JARVIS: {response}\n")

# Test 2: Intent parsing
print("=== Test 2: Intent Parsing ===")
commands = [
    "Turn on bedroom lights",
    "Turn off kitchen lights", 
    "What's the temperature?",
    "Is there motion in the living room?"
]

for cmd in commands:
    print(f"You: {cmd}")
    intent = llm.parse_intent(cmd)
    print(f"Intent: {intent}")
    print(f"JARVIS: {intent.get('response', 'Unknown')}\n")
