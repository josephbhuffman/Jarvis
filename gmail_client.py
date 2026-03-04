from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import base64
from email.mime.text import MIMEText

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class GmailClient:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail"""
        creds = None
        
        # Check if token exists
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
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_unread_count(self):
        """Get count of unread emails"""
        results = self.service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            q='is:unread'
        ).execute()
        
        messages = results.get('messages', [])
        return len(messages)
    
    def get_recent_emails(self, max_results=5):
        """Get recent emails"""
        results = self.service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            email_data = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = email_data.get('payload', {}).get('headers', [])
            email_info = {}
            
            for header in headers:
                if header['name'] == 'From':
                    email_info['from'] = header['value']
                elif header['name'] == 'Subject':
                    email_info['subject'] = header['value']
                elif header['name'] == 'Date':
                    email_info['date'] = header['value']
            
            # Check if unread
            labels = email_data.get('labelIds', [])
            email_info['unread'] = 'UNREAD' in labels
            
            emails.append(email_info)
        
        return emails
    
    def get_important_emails(self):
        """Get unread emails from important senders"""
        results = self.service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            q='is:unread'
        ).execute()
        
        messages = results.get('messages', [])
        important = []
        
        for msg in messages[:10]:  # Check last 10 unread
            email_data = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()
            
            headers = email_data.get('payload', {}).get('headers', [])
            email_info = {}
            
            for header in headers:
                if header['name'] == 'From':
                    email_info['from'] = header['value']
                elif header['name'] == 'Subject':
                    email_info['subject'] = header['value']
            
            important.append(email_info)
        
        return important
    
    def get_email_summary(self):
        """Get summary of inbox"""
        unread = self.get_unread_count()
        
        if unread == 0:
            return "No unread emails"
        elif unread == 1:
            emails = self.get_important_emails()
            if emails:
                return f"1 unread email from {emails[0]['from']}: {emails[0]['subject']}"
            return "1 unread email"
        else:
            return f"{unread} unread emails"

# Test
if __name__ == "__main__":
    gmail = GmailClient()
    
    print("Unread count:", gmail.get_unread_count())
    print("\nRecent emails:")
    
    emails = gmail.get_recent_emails(3)
    for email in emails:
        unread = "📧 [UNREAD]" if email.get('unread') else "📭"
        print(f"{unread} From: {email.get('from', 'Unknown')}")
        print(f"   Subject: {email.get('subject', 'No subject')}\n")
