from llm_client import JarvisLLM
from mqtt_client import JarvisMQTT
from alarm_system import AlarmSystem
from weather import WeatherAPI
from google_calendar import GoogleCalendar
from gmail_client import GmailClient
from intelligence import JarvisIntelligence
from scheduler import LightScheduler
import time
import requests
import subprocess
import os
import re
from datetime import datetime, timedelta
import logging
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Govee API key
GOVEE_API_KEY = "332fe7ca-0995-436d-ad33-c837ae8af443"

llm = JarvisLLM()
mqtt = JarvisMQTT()

voice_model = os.path.expanduser("~/.local/share/piper/voices/en_US-amy-medium.onnx")

def speak(text):
    """Make JARVIS speak out loud"""
    logger.info(f"🔊 Speaking: {text}")
    
    try:
        process = subprocess.Popen(
            ["/home/joseph/.local/bin/piper", "--model", voice_model, "--length-scale", "0.85", "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        audio_data, _ = process.communicate(input=text.encode())
        
        play_process = subprocess.Popen(
            ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
            stdin=subprocess.PIPE
        )
        play_process.communicate(input=audio_data)
    except Exception as e:
        logger.error(f"Speech error: {e}")

# Store device info
govee_device = None

# Initialize alarm system
alarm_system = AlarmSystem()

# Initialize weather
weather = WeatherAPI("d1973d164bd642c2b4805536262602")

# Initialize calendar
try:
    calendar = GoogleCalendar()
    logger.info("✅ Google Calendar connected")
except Exception as e:
    logger.error(f"⚠️ Calendar connection failed: {e}")
    calendar = None

# Initialize Gmail
try:
    gmail = GmailClient()
    logger.info("✅ Gmail connected")
except Exception as e:
    logger.error(f"⚠️ Gmail connection failed: {e}")
    gmail = None

# Initialize intelligence system
intelligence = JarvisIntelligence()
logger.info("✅ Intelligence system initialized")

# Initialize light scheduler
light_scheduler = LightScheduler()
logger.info("✅ Light scheduler initialized")

def on_alarm_trigger(alarm):
    """Called when alarm goes off"""
    logger.info(f"⏰ ALARM TRIGGERED: {alarm['label']}")
    
    # Turn on lights
    control_light('turn_on')
    
    # Get weather for wake-up
    weather_summary = weather.get_weather_summary()
    
    # Get calendar
    calendar_summary = ""
    if calendar:
        events = calendar.get_todays_events()
        if events:
            calendar_summary = f" You have {len(events)} event(s) today: {calendar.get_summary(events)}."
    
    # Speak wake-up message
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    
    wake_message = f"Good morning Joseph. It's {time_str}. {weather_summary}.{calendar_summary} Time to wake up."
    speak(wake_message)
    
    # Send to dashboard
    mqtt.publish("jarvis/response", f"Alarm: {alarm['label']}")

# Set the callback
alarm_system.on_alarm_trigger = on_alarm_trigger

# Set scheduler callback
def on_schedule_trigger(action, device):
    """Called when schedule triggers"""
    logger.info(f"⏰ Schedule triggered: {action} on {device or 'all lights'}")
    control_light(action, device)

light_scheduler.callback = on_schedule_trigger

def init_govee():
    global govee_device
    
    headers = {"Govee-API-Key": GOVEE_API_KEY}
    response = requests.get("https://developer-api.govee.com/v1/devices", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        devices = data.get('data', {}).get('devices', [])
        if devices:
            govee_device = devices
            logger.info(f"✅ Connected to {len(devices)} Govee devices:")
            for device in devices:
                logger.info(f"   - {device.get('deviceName')}")
            return True
    
    logger.error(f"❌ Govee connection failed: {response.status_code}")
    return False

def control_light(action, device_name=None):
    if not govee_device:
        logger.error("No Govee devices connected!")
        return False
    
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    # If specific device requested, find it
    if device_name:
        target_devices = [d for d in govee_device if device_name.lower() in d.get('deviceName', '').lower()]
        if not target_devices:
            logger.error(f"❌ Device '{device_name}' not found")
            return False
    else:
        # Control all devices
        target_devices = govee_device
    
    cmd = "turn"
    value = "on" if action == "turn_on" else "off"
    
    success_count = 0
    for device in target_devices:
        payload = {
            "device": device['device'],
            "model": device['model'],
            "cmd": {
                "name": cmd,
                "value": value
            }
        }
        
        response = requests.put(
            "https://developer-api.govee.com/v1/devices/control",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            success_count += 1
            logger.info(f"✅ {device.get('deviceName')} → {value}")
        else:
            logger.error(f"❌ {device.get('deviceName')} failed: {response.status_code}")
    
    return success_count > 0

def handle_command(topic, payload):
    command = payload
    
    logger.info(f"🎤 Command received: {command}")
    
    command_lower = command.lower()
    response = None
    
    # Log this command for learning
    intelligence.log_event('command', command, context={'source': 'chat'})
    
    # Check for weather commands
    if 'weather' in command_lower or 'temperature' in command_lower or 'forecast' in command_lower:
        if 'tomorrow' in command_lower and 'light' not in command_lower:
            forecast = weather.get_forecast(days=3)
            if forecast and len(forecast) > 1:
                tomorrow = forecast[1]
                response = f"Tomorrow will be {tomorrow['condition'].lower()} with a high of {int(tomorrow['max_temp_f'])}°F and a low of {int(tomorrow['min_temp_f'])}°F. {tomorrow['chance_of_rain']}% chance of rain."
            else:
                response = "I couldn't get the forecast right now."
        else:
            weather_summary = weather.get_weather_summary()
            response = weather_summary
        
        logger.info(f"🌤️ {response}")
    
    # Check for light schedule commands (BEFORE calendar and other checks!)
    elif (('light' in command_lower or 'lamp' in command_lower) and 
          ('schedule' in command_lower or 'show' in command_lower or 'list' in command_lower or 
           'tomorrow' in command_lower or 'every' in command_lower or 'daily' in command_lower)):
        
        if 'list' in command_lower or 'show' in command_lower:
            schedules = light_scheduler.get_schedules()
            if schedules:
                response = f"You have {len(schedules)} automatic light schedules:\n"
                for s in schedules:
                    days = s['days']
                    action = s['action'].replace('turn_', '')
                    response += f"\n- {s['time']}: Lights {action} ({days})"
            else:
                response = "No automatic light schedules"
        
        elif 'delete' in command_lower or 'remove' in command_lower or 'cancel' in command_lower:
            schedules = light_scheduler.get_schedules()
            if schedules:
                light_scheduler.delete_schedule(schedules[-1]['id'])
                response = "Automatic schedule removed"
            else:
                response = "No schedules to remove"
        
        elif 'on' in command_lower or 'off' in command_lower:
            # Extract time
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', command_lower)
            
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
                
                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                schedule_time = f"{hour:02d}:{minute:02d}"
                
                # Determine action
                action = 'turn_on' if 'on' in command_lower else 'turn_off'
                
                # Determine days
                if 'weekday' in command_lower:
                    days = 'weekdays'
                elif 'weekend' in command_lower:
                    days = 'weekends'
                elif 'every day' in command_lower or 'daily' in command_lower:
                    days = 'daily'
                else:
                    days = 'daily'  # Default to daily
                
                schedule = light_scheduler.add_schedule(schedule_time, action, days)
                response = f"Got it. I'll turn lights {action.replace('turn_', '')} at {schedule_time} {days}"
                logger.info(f"✅ {response}")
            else:
                response = "I couldn't understand that time. Try 'turn lights on tomorrow at 7:30 AM'"
        else:
            response = "Say 'turn lights on every day at 7:30 AM' or 'show my light schedules'"
        
        logger.info(f"⏰ {response}")
    
    # Check for calendar commands
    elif 'calendar' in command_lower or ('schedule' in command_lower and 'light' not in command_lower) or 'event' in command_lower:
        if not calendar:
            response = "Calendar not connected"
        elif 'tomorrow' in command_lower:
            events = calendar.get_tomorrows_events()
            if events:
                response = f"Tomorrow you have: {calendar.get_summary(events)}"
            else:
                response = "No events tomorrow"
        elif 'today' in command_lower:
            events = calendar.get_todays_events()
            if events:
                response = f"Today you have: {calendar.get_summary(events)}"
            else:
                response = "No events today"
        elif 'next' in command_lower:
            event = calendar.get_next_event()
            if event:
                response = f"Your next event is: {calendar.format_event(event)}"
            else:
                response = "No upcoming events"
        else:
            events = calendar.get_todays_events()
            if events:
                response = f"Today you have: {calendar.get_summary(events)}"
            else:
                response = "No events today"
        
        logger.info(f"📅 {response}")
    
    # Check for email commands
    elif 'email' in command_lower or 'inbox' in command_lower or 'mail' in command_lower:
        if not gmail:
            response = "Email not connected"
        else:
            response = gmail.get_email_summary()
        
        logger.info(f"📧 {response}")
    
    # Check for intelligence/learning commands
    elif 'pattern' in command_lower or 'learn' in command_lower or 'habit' in command_lower:
        patterns = intelligence.get_patterns()
        
        if not patterns:
            response = "I haven't detected any patterns yet. Keep using JARVIS and I'll learn your habits!"
        else:
            response = f"I've learned {len(patterns)} patterns:\n"
            for p in patterns[:5]:  # Show top 5
                ptype = p['type'].replace('_', ' ').title()
                conf = int(p['confidence'] * 100)
                response += f"\n- {ptype}: {conf}% confident"
        
        logger.info(f"🧠 {response}")
    
    # Check for alarm commands
    elif 'alarm' in command_lower or 'wake' in command_lower:
        if 'set' in command_lower:
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', command_lower)
            
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
                
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                alarm_time = f"{hour:02d}:{minute:02d}"
                alarm = alarm_system.add_alarm(alarm_time, "Morning Alarm")
                
                # Log alarm event for learning
                intelligence.log_event('alarm', 'set', 'morning', 
                                     {'alarm_time': alarm_time, 'day': datetime.now().strftime('%A')})
                
                response = f"Alarm set for {alarm_time}"
                logger.info(f"✅ {response}")
            else:
                response = "I couldn't understand that time. Try 'set alarm for 7 AM'"
                
        elif 'delete' in command_lower or 'cancel' in command_lower or 'remove' in command_lower:
            alarms = alarm_system.get_alarms()
            if alarms:
                enabled_alarms = [a for a in alarms if a['enabled']]
                if enabled_alarms:
                    alarm_system.delete_alarm(enabled_alarms[-1]['id'])
                    response = "Alarm deleted"
                else:
                    response = "No active alarms to delete"
            else:
                response = "No alarms to delete"
                
        elif 'list' in command_lower or 'show' in command_lower:
            alarms = alarm_system.get_alarms()
            if alarms:
                alarm_list = []
                for a in alarms:
                    if a['enabled']:
                        time_obj = datetime.fromisoformat(a['time'])
                        alarm_list.append(time_obj.strftime("%I:%M %p"))
                if alarm_list:
                    response = f"You have {len(alarm_list)} alarm: " + ", ".join(alarm_list)
                else:
                    response = "No active alarms"
            else:
                response = "No alarms set"
        else:
            response = "Say 'set alarm for 7 AM', 'list alarms', or 'delete alarm'"
    
    # Check for light control (immediate on/off)
    elif 'light' in command_lower or 'lamp' in command_lower:
        # Determine action
        if 'on' in command_lower or 'turn on' in command_lower:
            action = 'turn_on'
        elif 'off' in command_lower or 'turn off' in command_lower:
            action = 'turn_off'
        else:
            action = None
        
        if action:
            # Check if specific light mentioned
            device_name = None
            
            if 'all' in command_lower or 'both' in command_lower:
                device_name = None
            elif 'tall' in command_lower or 'light 1' in command_lower:
                device_name = 'tall'
            elif 'bed' in command_lower or 'side' in command_lower or 'light 2' in command_lower:
                device_name = 'bed'
            
            success = control_light(action, device_name)
            
            # Log light control event for learning
            if success:
                intelligence.log_event('light_control', action, device_name or 'all', 
                                     {'time': datetime.now().strftime('%H:%M')})
            
            if success:
                if action == 'turn_on':
                    logger.info(f"💡 LIGHTS TURNED ON!")
                    response = "Lights are now on"
                else:
                    logger.info(f"🌑 LIGHTS TURNED OFF!")
                    response = "Lights are now off"
            else:
                response = "Failed to control lights"
    
    # If no specific command matched, try LLM conversation
    if not response:
        logger.info(f"💬 Having conversation...")
        try:
            response = llm.conversation(command)
        except Exception as e:
            logger.error(f"⚠️ Conversation error: {e}")
            response = "I'm having trouble processing that request right now."
    
    # Check if JARVIS has any suggestions
    suggestion = intelligence.get_pending_suggestions()
    if suggestion:
        response += f"\n\nBy the way: {suggestion['text']}"
        intelligence.mark_suggestion(suggestion['id'], 'shown')
    
    # Send response back
    mqtt.publish("jarvis/response", response)
    logger.info(f"💬 JARVIS: {response}")
    speak(response)

# Initialize Govee
logger.info("Initializing Govee connection...")
init_govee()

# Connect to MQTT
mqtt.connect()
mqtt.subscribe("jarvis/command", handle_command)

logger.info("✅ JARVIS BRAIN is online!")
logger.info("🧠 LLM: Llama 3.2 (local)")
logger.info("📡 MQTT: Connected")
logger.info("💡 Govee: Ready")
logger.info("⏰ Alarms: Active")
logger.info("⏰ Scheduler: Active")
logger.info("🌤️ Weather: Connected")
logger.info("📅 Calendar: " + ("Connected" if calendar else "Offline"))
logger.info("📧 Gmail: " + ("Connected" if gmail else "Offline"))
logger.info("🤖 Intelligence: Learning")
logger.info("\nReady for commands!")

# Proactive intelligence check
def check_intelligence():
    """Check if JARVIS should proactively suggest something"""
    while True:
        time.sleep(300)  # Check every 5 minutes
        
        prediction = intelligence.predict_next_action()
        if prediction and prediction['confidence'] > 0.8:
            message = f"💡 {prediction['reason']} - would you like me to {prediction['action'].replace('_', ' ')}?"
            mqtt.publish("jarvis/suggestion", message)
            logger.info(f"🤖 Proactive suggestion: {message}")

# Start intelligence checker in background
intelligence_thread = threading.Thread(target=check_intelligence, daemon=True)
intelligence_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("\n👋 JARVIS shutting down...")
    alarm_system.running = False
    light_scheduler.running = False

