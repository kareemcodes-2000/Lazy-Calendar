# Required libraries
import os
import datetime
import dateparser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import tz
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

# Google Calendar API authentication
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('C:/Users/drake/OneDrive/Desktop/Coding Projects/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

service = authenticate_google_calendar()

# Formatting event date
def format_event_date(event_date):
    return event_date.strftime("%B %d, %Y at %I:%M %p") 

# Get event
def extract_event_details(command):
    try:
        # Split the command into date/time and event title
        date_part, event_title = command.split(', ', 1)
        
        # Parse the date and time
        event_date = dateparser.parse(date_part, settings={'RETURN_AS_TIMEZONE_AWARE': True})
        if not event_date:
            raise ValueError("Could not parse date and time from command.")
        
        # Convert the time to the Asia/Singapore time zone if not parsed correctly
        if event_date.tzinfo is None:
            event_date = event_date.replace(tzinfo=tz.gettz('Asia/Singapore'))
        
        return event_title, event_date
    except ValueError as e:
        raise ValueError(str(e))

# Add event to Google Calendar (Function)
def add_event_to_calendar(service, summary, description, start_time, end_time):
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Singapore',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Singapore',
        }
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")

# Get events for the next week
def get_next_week_events():
    now = datetime.now()
    one_week_later = now + timedelta(days=7)
    events_result = service.events().list(
        calendarId='primary', timeMin=now.isoformat() + 'Z',
        timeMax=one_week_later.isoformat() + 'Z', singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return "You have no events next week."

    # Format the output
    response = f"Next week, you have {len(events)} event(s): "
    for event in events:
        event_title = event['summary']
        start_time = datetime.fromisoformat(event['start']['dateTime'])
        response += f"{event_title} on {format_event_date(start_time)}; "
    
    return response.strip('; ')

# Kivvy portion
class EventApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        # Enter command
        self.command_input = TextInput(hint_text='Enter your event like this: date,month,year, time, activity', multiline=True, size_hint=(1, 0.6))
        self.add_widget(self.command_input)

        # Command entry
        self.add_button = Button(text="Add Event(s) to Calendar", size_hint=(1, 0.2))
        self.add_button.bind(on_press=self.add_event)
        self.add_widget(self.add_button)

        # Label to show status
        self.status_label = Label(text="")
        self.add_widget(self.status_label)

        # Next week event button
        self.check_button = Button(text="Check Next Week's Events", size_hint=(1, 0.2))
        self.check_button.bind(on_press=self.check_next_week_events)
        self.add_widget(self.check_button)

    def add_event(self, instance):
        commands = self.command_input.text.strip().splitlines()  # Split input into lines
        errors = []
        success_count = 0

        for command in commands:
            try:
                title, event_date = extract_event_details(command)
                start_time = event_date.strftime("%Y-%m-%dT%H:%M:%S")
                end_time = (event_date + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
                add_event_to_calendar(service, title, "Event added via app", start_time, end_time)
                success_count += 1
            except Exception as e:
                errors.append(f"Error with event: {command} - {str(e)}")

        if errors:
            self.status_label.text = f"{success_count} events added. Errors: {', '.join(errors)}"
        else:
            self.status_label.text = f"Successfully added {success_count} events!"

    def check_next_week_events(self, instance):
        events_summary = get_next_week_events()
        self.status_label.text = events_summary

class CalendarApp(App):
    def build(self):
        return EventApp()

if __name__ == '__main__':
    CalendarApp().run()
