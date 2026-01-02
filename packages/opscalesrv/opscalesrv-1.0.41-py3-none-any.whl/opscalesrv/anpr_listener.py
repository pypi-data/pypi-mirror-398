
import http.server
import socketserver
import threading
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Global storage for the latest captured plates per listener
# Structure: {listener_url: {'plate': '...', 'timestamp': datetime_obj, 'captured_at': datetime_obj, 'xml_content': '...', 'plate_tag': '...', 'response_tag': '...'}}
LISTENER_PLATES = {}

PLATE_CALLBACK = None

def register_callback(func):
    global PLATE_CALLBACK
    PLATE_CALLBACK = func



def process_anpr_xml(xml_data, config, listener_url=None):
    """
    Process ANPR XML data and update global state
    """
    global LISTENER_PLATES
    
    # Use listener URL as key, or default key if not provided
    if not listener_url:
        listener_url = config.get('url', '/anpr/notify')
    
    # Initialize if not exists
    if listener_url not in LISTENER_PLATES:
        LISTENER_PLATES[listener_url] = {
            'plate': None,
            'timestamp': None,
            'captured_at': None,
            'xml_content': None,
            'plate_tag': None,
            'response_tag': None,
            'last_received_xml': None,
            'last_received_at': None
        }
    
    listener_data = LISTENER_PLATES[listener_url]
    
    # Always update raw content for debugging/test view
    listener_data['last_received_xml'] = xml_data
    listener_data['last_received_at'] = datetime.now()

    try:
        # Parse XML
        root = ET.fromstring(xml_data)
        
        plate_tag = config.get('plate_tag', 'licensePlate')
        tolerance_min = config.get('tolerance_minutes', 5)
        
        # Extract Plate
        plate = "NO_PLATE"
        # Namespace insensitive search
        for elem in root.iter():
            if plate_tag in elem.tag and elem.text:
                plate = elem.text.strip()
                break
        
        if plate == "NO_PLATE":
            logger.debug("No plate found in incoming XML")
            return

        # Extract Timestamp
        # Cameras often use 'dateTime' or 'absTime'
        # We will search for common time tags
        xml_time = None
        time_str = ""
        for tag in ['dateTime', 'absTime', 'captureTime', 'Timestamp']:
            found = False
            for elem in root.iter():
                if tag in elem.tag and elem.text:
                    time_str = elem.text.strip()
                    found = True
                    break
            if found:
                break
        
        if not time_str:
            logger.warning("No timestamp found in ANPR XML")
            return

        # Parse timestamp (Try common formats)
        try:
            # Remove fractional seconds for simpler parsing if needed, or handle them
            # Removing Z for now to handle simple naive comparison (assuming local time or UTC consistency)
            clean_time_str = time_str.split('.')[0].replace('Z', '')
            xml_time = datetime.strptime(clean_time_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.error(f"Could not parse timestamp: {time_str}")
            return

        # Validate Time
        now = datetime.now()
        # If xml_time is naive, assume it's system local time (or camera is synced)
        # Calculate difference
        diff = abs((now - xml_time).total_seconds()) / 60.0
        
        if diff <= tolerance_min:
            logger.info(f"ANPR Listener: Accepted plate {plate} (Time diff: {diff:.2f} min)")
            listener_data['plate'] = plate
            listener_data['timestamp'] = xml_time
            listener_data['captured_at'] = now
            listener_data['xml_content'] = xml_data
            listener_data['plate_tag'] = plate_tag
            listener_data['response_tag'] = config.get('response_tag', '')
            
            if PLATE_CALLBACK:
                try:
                    PLATE_CALLBACK(plate)
                except Exception as e:
                    logger.error(f"Error in ANPR callback: {e}")
        else:
            logger.warning(f"ANPR Listener: Ignored plate {plate} - Time out of tolerance ({diff:.2f} > {tolerance_min} min)")

    except Exception as e:
        logger.error(f"Error parsing ANPR XML body: {e}")


def get_latest_plate(listener_url=None):
    """
    Get latest plate for a specific listener, or all listener plates
    """
    if listener_url:
        return LISTENER_PLATES.get(listener_url, {
            'plate': None,
            'timestamp': None,
            'captured_at': None,
            'xml_content': None,
            'plate_tag': None,
            'response_tag': None
        })
    else:
        # Return all listener plates
        return LISTENER_PLATES
    
def get_all_listener_plates():
    """
    Get all listener plates as a dictionary
    """
    return LISTENER_PLATES

