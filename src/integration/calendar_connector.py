import os
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarConnector:
    """
    Handles interactions with the Google Calendar API.
    """
    def __init__(self):
        self.creds = None
        self.service = None
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self._authenticate()

    def _authenticate(self):
        """Authenticates with Google Calendar API using token.json or credentials.json."""
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"[Calendar] Error refreshing token: {e}")
                    self.creds = None
            
            if not self.creds:
                if os.path.exists('credentials.json'):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', SCOPES)
                        # This will open a browser window for authentication
                        # In a headless server environment, this part needs to be done once locally to generate token.json
                        # Using port 8080 to match "Web Application" redirect URI
                        self.creds = flow.run_local_server(port=8080)
                        # Save the credentials for the next run
                        with open('token.json', 'w') as token:
                            token.write(self.creds.to_json())
                    except Exception as e:
                        print(f"[Calendar] Error during authentication flow: {e}")
                else:
                    print("[Calendar] Warning: 'credentials.json' not found. Calendar integration disabled.")

        if self.creds:
            try:
                self.service = build('calendar', 'v3', credentials=self.creds)
                print("[Calendar] Authenticated successfully.")
            except Exception as e:
                print(f"[Calendar] Failed to build service: {e}")
                self.service = None

    def add_event(self, event):
        """Adds an event to the Google Calendar."""
        if not self.service:
            return False

        try:
            # Convert datetime to ISO format for Google Calendar
            # Google Calendar expects '2023-10-26T09:00:00-07:00'
            start_dt = event.start_time
            if not start_dt.tzinfo:
                 # Assume local time if naive, or UTC? Let's assume input is correct for now
                 # Ideally we should handle timezones properly.
                 pass
            
            end_dt = event.end_time
            if not end_dt:
                # Default to 1 hour duration if no end time
                end_dt = start_dt + datetime.timedelta(hours=1)

            # determine reminder offsets (minutes before event)
            # default to one week (10080 min) plus the existing 1‑hour popup
            week_offset = int(os.getenv("CALENDAR_REMINDER_MINUTES", "10080"))
            overrides = []
            if week_offset > 0:
                overrides.append({'method': 'popup', 'minutes': week_offset})
            # always keep a 1‑hour reminder as fallback
            if week_offset != 60:
                overrides.append({'method': 'popup', 'minutes': 60})

            event_body = {
                'summary': event.title,
                'location': event.venue,
                'description': f"{event.description or ''}\n\nSource: {event.source}\nImpact: {event.impact_score}",
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': overrides,
                },
            }

            event_result = self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
            print(f"[Calendar] Event created: {event_result.get('htmlLink')}")
            return event_result.get('id')

        except HttpError as error:
            print(f"[Calendar] An error occurred: {error}")
            return None
        except Exception as e:
            print(f"[Calendar] Unexpected error: {e}")
            return None

    def delete_event(self, event_id: str):
        """Deletes an event from the Google Calendar."""
        if not self.service or not event_id:
            return False

        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            print(f"[Calendar] Event deleted: {event_id}")
            return True
        except HttpError as error:
            if error.resp.status == 410 or error.resp.status == 404:
                print(f"[Calendar] Event {event_id} already gone.")
                return True # Consider successful
            print(f"[Calendar] Delete error: {error}")
            return False
        except Exception as e:
            print(f"[Calendar] Unexpected delete error: {e}")
            return False
