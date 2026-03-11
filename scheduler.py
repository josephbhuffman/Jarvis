import json
import os
from datetime import datetime, time as time_type
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightScheduler:
    def __init__(self, schedule_file='light_schedules.json'):
        self.schedule_file = schedule_file
        self.schedules = self._load_schedules()
        self.running = True
        self.callback = None
        
        # Start scheduler thread
        self.thread = threading.Thread(target=self._check_schedules, daemon=True)
        self.thread.start()
    
    def _load_schedules(self):
        """Load schedules from file"""
        if os.path.exists(self.schedule_file):
            with open(self.schedule_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_schedules(self):
        """Save schedules to file"""
        with open(self.schedule_file, 'w') as f:
            json.dump(self.schedules, f, indent=2)
    
    def add_schedule(self, time_str, action, days='daily', device=None):
        """
        Add a light schedule
        time_str: "07:30" (24-hour format)
        action: "turn_on" or "turn_off"
        days: "daily", "weekdays", "weekends", or list like ["monday", "wednesday"]
        device: specific device or None for all
        """
        schedule = {
            'id': len(self.schedules) + 1,
            'time': time_str,
            'action': action,
            'days': days,
            'device': device,
            'enabled': True
        }
        
        self.schedules.append(schedule)
        self._save_schedules()
        return schedule
    
    def delete_schedule(self, schedule_id):
        """Delete a schedule by ID"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self._save_schedules()
    
    def get_schedules(self):
        """Get all schedules"""
        return [s for s in self.schedules if s['enabled']]
    
    def _should_run_today(self, schedule):
        """Check if schedule should run today"""
        now = datetime.now()
        weekday = now.strftime('%A').lower()
        
        days = schedule['days']
        
        if days == 'daily':
            return True
        elif days == 'weekdays':
            return now.weekday() < 5
        elif days == 'weekends':
            return now.weekday() >= 5
        elif isinstance(days, list):
            return weekday in [d.lower() for d in days]
        
        return False
    
    def _check_schedules(self):
        """Background thread that checks schedules"""
        last_minute = None
        
        while self.running:
            now = datetime.now()
            current_minute = now.strftime('%H:%M')
            
            # Only check once per minute
            if current_minute != last_minute:
                last_minute = current_minute
                
                for schedule in self.get_schedules():
                    if schedule['time'] == current_minute:
                        if self._should_run_today(schedule):
                            # Trigger the action
                            if self.callback:
                                logger.info(f"⏰ Schedule triggered: {schedule['action']} at {schedule['time']}")
                                self.callback(schedule['action'], schedule.get('device'))
            
            time.sleep(30)  # Check every 30 seconds

# Test
if __name__ == "__main__":
    def test_callback(action, device):
        print(f"Would execute: {action} on {device or 'all lights'}")
    
    scheduler = LightScheduler()
    scheduler.callback = test_callback
    
    # Add test schedules
    scheduler.add_schedule("07:30", "turn_on", "weekdays")
    scheduler.add_schedule("22:00", "turn_off", "daily")
    
    print("Schedules:")
    for s in scheduler.get_schedules():
        print(f"- {s['time']}: {s['action']} ({s['days']})")
    
    print("\nScheduler running... (Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped")
