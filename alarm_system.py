import json
import os
from datetime import datetime, timedelta
import threading
import time

class AlarmSystem:
    def __init__(self, storage_file="alarms.json"):
        self.storage_file = storage_file
        self.alarms = []
        self.load_alarms()
        self.running = True
        
        # Start alarm checker thread
        self.checker_thread = threading.Thread(target=self.check_alarms, daemon=True)
        self.checker_thread.start()
    
    def load_alarms(self):
        """Load alarms from file"""
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                self.alarms = json.load(f)
        else:
            self.alarms = []
    
    def save_alarms(self):
        """Save alarms to file"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.alarms, f, indent=2)
    
    def add_alarm(self, alarm_time, label="Alarm", recurring=None):
        """Add a new alarm
        
        Args:
            alarm_time: datetime object or string like "07:00"
            label: Description of alarm
            recurring: None, "daily", "weekdays", "weekends"
        """
        if isinstance(alarm_time, str):
            # Parse "07:00" format
            hour, minute = map(int, alarm_time.split(':'))
            alarm_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time already passed today, set for tomorrow
            if alarm_time < datetime.now():
                alarm_time += timedelta(days=1)
        
        alarm = {
            "id": len(self.alarms) + 1,
            "time": alarm_time.isoformat(),
            "label": label,
            "enabled": True,
            "recurring": recurring,
            "snoozed": False
        }
        
        self.alarms.append(alarm)
        self.save_alarms()
        
        return alarm
    
    def delete_alarm(self, alarm_id):
        """Delete alarm by ID"""
        self.alarms = [a for a in self.alarms if a['id'] != alarm_id]
        self.save_alarms()
        return True
    
    def get_alarms(self):
        """Get all alarms"""
        return self.alarms
    
    def get_next_alarm(self):
        """Get the next alarm that will go off"""
        now = datetime.now()
        upcoming = []
        
        for alarm in self.alarms:
            if not alarm['enabled']:
                continue
                
            alarm_time = datetime.fromisoformat(alarm['time'])
            if alarm_time > now:
                upcoming.append((alarm_time, alarm))
        
        if upcoming:
            upcoming.sort(key=lambda x: x[0])
            return upcoming[0][1]
        return None
    
    def snooze_alarm(self, alarm_id, minutes=10):
        """Snooze an alarm"""
        for alarm in self.alarms:
            if alarm['id'] == alarm_id:
                current_time = datetime.fromisoformat(alarm['time'])
                new_time = current_time + timedelta(minutes=minutes)
                alarm['time'] = new_time.isoformat()
                alarm['snoozed'] = True
                self.save_alarms()
                return new_time
        return None
    
    def check_alarms(self):
        """Background thread that checks for alarms"""
        while self.running:
            now = datetime.now()
            
            for alarm in self.alarms:
                if not alarm['enabled']:
                    continue
                
                alarm_time = datetime.fromisoformat(alarm['time'])
                
                # Check if alarm should trigger (within 30 seconds)
                time_diff = (alarm_time - now).total_seconds()
                
                if 0 <= time_diff <= 30:
                    self.trigger_alarm(alarm)
                    
                    # Handle recurring
                    if alarm['recurring'] == 'daily':
                        alarm['time'] = (alarm_time + timedelta(days=1)).isoformat()
                    elif alarm['recurring'] == 'weekdays' and now.weekday() < 4:
                        alarm['time'] = (alarm_time + timedelta(days=1)).isoformat()
                    elif alarm['recurring'] == 'weekends' and now.weekday() >= 5:
                        alarm['time'] = (alarm_time + timedelta(days=1)).isoformat()
                    else:
                        # One-time alarm, disable it
                        alarm['enabled'] = False
                    
                    alarm['snoozed'] = False
                    self.save_alarms()
            
            time.sleep(30)  # Check every 30 seconds
    
    def trigger_alarm(self, alarm):
        """Called when alarm goes off"""
        print(f"\n🔔 ALARM: {alarm['label']} at {alarm['time']}")
        # This will be called by JARVIS to execute wake-up routine
        self.on_alarm_trigger(alarm)
    
    def on_alarm_trigger(self, alarm):
        """Override this in jarvis_brain.py"""
        pass

# For testing
if __name__ == "__main__":
    alarm_system = AlarmSystem()
    
    # Test: Set alarm for 1 minute from now
    test_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    alarm_system.add_alarm(test_time, "Test Alarm")
    
    print(f"Alarm set for {test_time}")
    print("Waiting for alarm...")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
