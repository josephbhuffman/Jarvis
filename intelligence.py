import sqlite3
from datetime import datetime, timedelta
import json
from collections import defaultdict

class JarvisIntelligence:
    def __init__(self, db_file='jarvis_intelligence.db'):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        
        # Event log - records EVERYTHING
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                action TEXT NOT NULL,
                context TEXT,
                metadata TEXT
            )
        ''')
        
        # Patterns - detected behavior patterns
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL,
                last_seen TEXT,
                occurrences INTEGER DEFAULT 1
            )
        ''')
        
        # Suggestions - automation suggestions
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_type TEXT NOT NULL,
                suggestion_text TEXT NOT NULL,
                pattern_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        ''')
        
        # User preferences - learned preferences
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                confidence REAL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def log_event(self, event_type, action, context=None, metadata=None):
        """Log any event that happens"""
        timestamp = datetime.now().isoformat()
        
        # Convert context and metadata to JSON strings
        context_json = json.dumps(context) if context else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.cursor.execute('''
            INSERT INTO events (timestamp, event_type, action, context, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, event_type, action, context_json, metadata_json))
        
        self.conn.commit()
        
        # Check for patterns after logging
        self._analyze_patterns(event_type, action)
    
    def _analyze_patterns(self, event_type, action):
        """Analyze recent events for patterns"""
        
        # Get last 30 days of this event type
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        self.cursor.execute('''
            SELECT timestamp, action, context
            FROM events
            WHERE event_type = ? AND timestamp > ?
            ORDER BY timestamp DESC
        ''', (event_type, thirty_days_ago))
        
        events = self.cursor.fetchall()
        
        if len(events) < 3:
            return  # Not enough data
        
        # Detect time-based patterns
        if event_type == 'light_control':
            self._detect_light_patterns(events, action)
        elif event_type == 'alarm':
            self._detect_alarm_patterns(events)
    
    def _detect_light_patterns(self, events, action):
        """Detect patterns in light usage"""
        
        # Group by action (on/off)
        action_events = [e for e in events if e[1] == action]
        
        if len(action_events) < 5:
            return
        
        # Extract times
        times = []
        for event in action_events[:14]:  # Last 2 weeks
            dt = datetime.fromisoformat(event[0])
            times.append(dt.hour * 60 + dt.minute)  # Minutes since midnight
        
        # Calculate average time
        avg_time = sum(times) / len(times)
        
        # Calculate variance
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        
        # If consistent (low variance), it's a pattern
        if std_dev < 30:  # Within 30 minutes variance
            hours = int(avg_time // 60)
            minutes = int(avg_time % 60)
            
            pattern_data = {
                'action': action,
                'time': f"{hours:02d}:{minutes:02d}",
                'variance': std_dev,
                'device': 'lights'
            }
            
            confidence = min(0.9, len(action_events) / 14.0)  # Max 90% confidence
            
            # Store or update pattern
            self._store_pattern('light_schedule', pattern_data, confidence)
    
    def _detect_alarm_patterns(self, events):
        """Detect patterns in alarm setting"""
        
        # Group by day of week
        weekday_alarms = defaultdict(list)
        weekend_alarms = []
        
        for event in events[:30]:  # Last 30 alarms
            dt = datetime.fromisoformat(event[0])
            
            # Parse metadata if exists
            try:
                metadata = json.loads(event[2]) if event[2] else {}
            except:
                metadata = {}
            
            alarm_time = metadata.get('alarm_time')
            if not alarm_time:
                continue
            
            if dt.weekday() < 5:  # Weekday
                weekday_alarms[dt.weekday()].append(alarm_time)
            else:  # Weekend
                weekend_alarms.append(alarm_time)
        
        # Detect weekday pattern
        if weekday_alarms:
            all_weekday_times = [t for times in weekday_alarms.values() for t in times]
            if len(all_weekday_times) >= 3:
                # Most common weekday alarm
                from collections import Counter
                common_time = Counter(all_weekday_times).most_common(1)[0][0]
                
                pattern_data = {
                    'day_type': 'weekday',
                    'time': common_time,
                    'frequency': len(all_weekday_times)
                }
                
                confidence = min(0.85, len(all_weekday_times) / 20.0)
                self._store_pattern('alarm_schedule', pattern_data, confidence)
    
    def _store_pattern(self, pattern_type, pattern_data, confidence):
        """Store or update a detected pattern"""
        
        pattern_json = json.dumps(pattern_data)
        timestamp = datetime.now().isoformat()
        
        # Check if pattern exists
        self.cursor.execute('''
            SELECT id, occurrences FROM patterns
            WHERE pattern_type = ? AND pattern_data = ?
        ''', (pattern_type, pattern_json))
        
        existing = self.cursor.fetchone()
        
        if existing:
            # Update existing pattern
            pattern_id, occurrences = existing
            self.cursor.execute('''
                UPDATE patterns
                SET confidence = ?, last_seen = ?, occurrences = ?
                WHERE id = ?
            ''', (confidence, timestamp, occurrences + 1, pattern_id))
        else:
            # Insert new pattern
            self.cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_data, confidence, last_seen)
                VALUES (?, ?, ?, ?)
            ''', (pattern_type, pattern_json, confidence, timestamp))
            
            pattern_id = self.cursor.lastrowid
            
            # Generate suggestion for new pattern
            self._generate_suggestion(pattern_id, pattern_type, pattern_data, confidence)
        
        self.conn.commit()
    
    def _generate_suggestion(self, pattern_id, pattern_type, pattern_data, confidence):
        """Generate automation suggestion from pattern"""
        
        if confidence < 0.6:
            return  # Not confident enough
        
        suggestion_text = None
        
        if pattern_type == 'light_schedule':
            action = pattern_data['action']
            time = pattern_data['time']
            suggestion_text = f"I noticed you usually turn lights {action.replace('turn_', '')} around {time}. Want me to do that automatically?"
        
        elif pattern_type == 'alarm_schedule':
            day_type = pattern_data['day_type']
            time = pattern_data['time']
            suggestion_text = f"You usually set your alarm for {time} on {day_type}s. Should I set it automatically?"
        
        if suggestion_text:
            timestamp = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO suggestions (suggestion_type, suggestion_text, pattern_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (pattern_type, suggestion_text, pattern_id, timestamp))
            
            self.conn.commit()
    
    def get_pending_suggestions(self):
        """Get suggestions that haven't been shown yet"""
        self.cursor.execute('''
            SELECT id, suggestion_type, suggestion_text, pattern_id
            FROM suggestions
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
        ''')
        
        result = self.cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'type': result[1],
                'text': result[2],
                'pattern_id': result[3]
            }
        return None
    
    def mark_suggestion(self, suggestion_id, status):
        """Mark suggestion as accepted/rejected/shown"""
        self.cursor.execute('''
            UPDATE suggestions
            SET status = ?
            WHERE id = ?
        ''', (status, suggestion_id))
        
        self.conn.commit()
    
    def get_patterns(self, pattern_type=None):
        """Get detected patterns"""
        if pattern_type:
            self.cursor.execute('''
                SELECT pattern_type, pattern_data, confidence, last_seen, occurrences
                FROM patterns
                WHERE pattern_type = ?
                ORDER BY confidence DESC
            ''', (pattern_type,))
        else:
            self.cursor.execute('''
                SELECT pattern_type, pattern_data, confidence, last_seen, occurrences
                FROM patterns
                ORDER BY confidence DESC
            ''')
        
        patterns = []
        for row in self.cursor.fetchall():
            patterns.append({
                'type': row[0],
                'data': json.loads(row[1]),
                'confidence': row[2],
                'last_seen': row[3],
                'occurrences': row[4]
            })
        
        return patterns
    
    def predict_next_action(self):
        """Predict what the user might want next"""
        
        now = datetime.now()
        current_time = now.hour * 60 + now.minute
        
        # Check light patterns
        light_patterns = self.get_patterns('light_schedule')
        
        for pattern in light_patterns:
            if pattern['confidence'] < 0.7:
                continue
            
            data = pattern['data']
            pattern_time = data['time']
            hours, minutes = map(int, pattern_time.split(':'))
            pattern_minutes = hours * 60 + minutes
            
            # If within 5 minutes of pattern time
            if abs(current_time - pattern_minutes) < 5:
                return {
                    'type': 'light_control',
                    'action': data['action'],
                    'confidence': pattern['confidence'],
                    'reason': f"You usually do this around {pattern_time}"
                }
        
        return None

# Test
if __name__ == "__main__":
    intel = JarvisIntelligence()
    
    # Simulate some events
    print("Logging test events...")
    intel.log_event('light_control', 'turn_off', context={'room': 'bedroom'}, metadata={'device': 'all_lights'})
    
    # Check patterns
    patterns = intel.get_patterns()
    print(f"\nDetected {len(patterns)} patterns")
    
    for p in patterns:
        print(f"- {p['type']}: {p['data']} (confidence: {p['confidence']:.0%})")
    
    # Check suggestions
    suggestion = intel.get_pending_suggestions()
    if suggestion:
        print(f"\n💡 Suggestion: {suggestion['text']}")
