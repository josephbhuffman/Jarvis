from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class GoogleCalendar:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar"""
        creds = None
        
        # Check if token already exists
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_todays_events(self):
        """Get today's calendar events"""
        now = datetime.datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=today_start,
            timeMax=today_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    
    def get_tomorrows_events(self):
        """Get tomorrow's calendar events"""
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=tomorrow_start,
            timeMax=tomorrow_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    
    def get_upcoming_events(self, days=7):
        """Get upcoming events for next N days"""
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        end = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    
    def get_next_event(self):
        """Get the next upcoming event"""
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=1,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events[0] if events else None
    
    def format_event(self, event):
        """Format event for display"""
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'No title')
        
        # Parse time
        if 'T' in start:  # Has time
            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M %p')
            return f"{summary} at {time_str}"
        else:  # All day event
            return f"{summary} (all day)"
    
    def get_summary(self, events):
        """Get text summary of events"""
        if not events:
            return "No events"
        
        summary = []
        for event in events:
            summary.append(self.format_event(event))
        
        return ", ".join(summary)

# Test
if __name__ == "__main__":
    cal = GoogleCalendar()
    
    print("Today's events:")
    today = cal.get_todays_events()
    print(cal.get_summary(today))
    
    print("\nTomorrow's events:")
    tomorrow = cal.get_tomorrows_events()
    print(cal.get_summary(tomorrow))
