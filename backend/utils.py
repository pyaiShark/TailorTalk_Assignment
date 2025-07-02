import os
import json
import logging
from datetime import datetime, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re



def get_calendar_service():
    try:
        # Get JSON string from environment
        creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        
        # Log the value for debugging
        logging.info(f"Credentials length: {len(creds_json)}")
        logging.info(f"First 100 characters: {creds_json[:100]}")
        
        # Validate JSON is not empty
        if not creds_json:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is empty")
        
        # Parse JSON
        try:
            service_account_info = json.loads(creds_json)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON: {str(e)}")
            logging.error(f"Problematic content: {creds_json[:200]}")
            raise
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        return build('calendar', 'v3', credentials=credentials)
        
    except Exception as e:
        logging.exception("Failed to create calendar service")
        raise RuntimeError(f"Failed to create calendar service: {str(e)}")

def get_calendar_id():
    """Get calendar ID from environment"""
    calendar_id = os.getenv("CALENDAR_ID")
    if not calendar_id:
        raise ValueError("CALENDAR_ID environment variable not set")
    return calendar_id

def format_rfc3339(dt_str):
    """Convert date string to RFC3339 format with timezone"""

    # Check if already properly formatted
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})", dt_str):
        return dt_str
    
    try:
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                return dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                continue

        # If all cases fail, assume UTC and append Z
        return dt_str + "Z"
    except Exception:
        # Fallback to UTC if parsing fails
        return dt_str + "Z"

def check_availability(service, calendar_id, start_time, end_time):
    """Check available slots in calendar"""
    try:
        start_time = format_rfc3339(start_time)
        end_time = format_rfc3339(end_time)
        
        print(f"Checking availability: calendar_id={calendar_id}, start={start_time}, end={end_time}")
        
        events = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events.get('items', [])
    except HttpError as error:
        print(f"Google Calendar API error: {error}")
        return []
    except Exception as e:
        print(f"General error checking availability: {str(e)}")
        return []

def book_appointment(service, calendar_id, summary, start_time, end_time):
    """Book appointment on calendar"""
    try:
        start_time = format_rfc3339(start_time)
        end_time = format_rfc3339(end_time)
        
        print(f"Booking appointment: calendar_id={calendar_id}, summary={summary}, start={start_time}, end={end_time}")
        
        event = {
            'summary': summary,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time}
        }
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        return created_event['id']
    except HttpError as error:
        print(f"Google Calendar API error: {error}")
        return None
    except Exception as e:
        print(f"General error booking appointment: {str(e)}")
        return None
