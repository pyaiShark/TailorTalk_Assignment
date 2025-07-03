import os
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import pytz

# Configuration
BUSINESS_HOURS = (9, 17)
SLOT_DURATION = 30

def get_calendar_service():
    """Initialize and return Google Calendar service"""
    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not service_account_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    try:
        credentials = Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        return build('calendar', 'v3', credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Failed to create calendar service: {str(e)}")

def get_calendar_id():
    """Get calendar ID from environment"""
    calendar_id = os.getenv("CALENDAR_ID")
    if not calendar_id:
        raise ValueError("CALENDAR_ID environment variable not set")
    return calendar_id

def get_calendar_timezone(service, calendar_id):
    """Get calendar's timezone"""
    try:
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        return calendar.get('timeZone', 'UTC')
    except Exception as e:
        print(f"Error getting calendar timezone: {str(e)}")
        return 'UTC'

def format_rfc3339(dt_str):
    """Convert date string to RFC3339 format with timezone"""
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
    """
    Check available time slots in calendar between business hours.
    Returns list of available slots in 12-hour format.
    """
    try:
        start_time = format_rfc3339(start_time)
        end_time = format_rfc3339(end_time)
        
        # Get calendar timezone
        tz_str = get_calendar_timezone(service, calendar_id)
        tz = pytz.timezone(tz_str)
        
        # Convert to datetime objects
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
        
        # Adjust to business hours in calendar timezone
        start_local = start_dt.astimezone(tz)
        end_local = end_dt.astimezone(tz)
        
        # Create business hour boundaries
        business_start = start_local.replace(
            hour=BUSINESS_HOURS[0], 
            minute=0, 
            second=0, 
            microsecond=0
        )
        business_end = start_local.replace(
            hour=BUSINESS_HOURS[1], 
            minute=0, 
            second=0, 
            microsecond=0
        )
        
        # Get busy events
        events = service.events().list(
            calendarId=calendar_id,
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute().get('items', [])
        
        # Convert events to UTC for comparison
        busy_slots = []
        for event in events:
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            event_end = event['end'].get('dateTime', event['end'].get('date'))
            
            if 'date' in event['start']:  # All-day event
                event_start_dt = datetime.fromisoformat(event_start).replace(tzinfo=timezone.utc)
                event_end_dt = datetime.fromisoformat(event_end).replace(tzinfo=timezone.utc)
                busy_slots.append((event_start_dt, event_end_dt))
            else:  # Timed event
                event_start_dt = datetime.fromisoformat(event_start).replace(tzinfo=timezone.utc)
                event_end_dt = datetime.fromisoformat(event_end).replace(tzinfo=timezone.utc)
                busy_slots.append((event_start_dt, event_end_dt))
        
        # Generate time slots
        available_slots = []
        current = business_start
        while current < business_end:
            slot_end = current + timedelta(minutes=SLOT_DURATION)
            if slot_end > business_end:
                break
                
            # Convert to UTC for comparison
            slot_start_utc = current.astimezone(timezone.utc)
            slot_end_utc = slot_end.astimezone(timezone.utc)
            
            # Check if slot is available
            slot_available = True
            for busy_start, busy_end in busy_slots:
                if busy_start < slot_end_utc and busy_end > slot_start_utc:
                    slot_available = False
                    break
            
            if slot_available:
                # Format in 12-hour time
                start_str = current.strftime("%I:%M %p").lstrip('0')
                end_str = slot_end.strftime("%I:%M %p").lstrip('0')
                available_slots.append(f"{start_str} - {end_str}")
            
            current = slot_end
        
        return available_slots
        
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
        
        event = {
            'summary': summary,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time}
        }
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        return created_event.get('id', 'Success')
    except HttpError as error:
        print(f"Google Calendar API error: {error}")
        return None
    except Exception as e:
        print(f"General error booking appointment: {str(e)}")
        return None
