#!/usr/bin/env python3
import requests
from requests.auth import HTTPDigestAuth
import logging
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Cache structure: { 'entrance': { 'plate': '...', 'timestamp': ..., 'status': ... }, 'exit': ... }
_PLATE_CACHE = {}


def fetch_and_log_xml(path, config):
    """
    Gelen path'e göre ilgili kameradan XML verisini çeker, loglar ve plakayı parse eder.
    """
    anpr_config = config.get('anpr', {})
    if not anpr_config.get('enabled', False):
        return "ANPR_DISABLED", 0



    # Path kontrolü
    target_key = None
    path_lower = path.lower().split('?')[0]
    
    if path_lower == '/' or 'entrance' in path_lower:
        target_key = 'entrance'
    elif 'exit' in path_lower:
        target_key = 'exit'
    
    if not target_key or target_key not in anpr_config:
        return "NO_DIRECTIONS", 0


    cam_settings = anpr_config[target_key]
    
    # Check if this specific camera is enabled
    if not cam_settings.get('enabled', True):
        logger.info(f"ANPR fetching skipped: {target_key} camera is disabled in config")
        return "DIRECTION_DISABLED", 0


    server = cam_settings.get('server')
    port = cam_settings.get('port', 80)
    url_path = cam_settings.get('URL', '/ISAPI/Event/notification/alertStream')
    username = cam_settings.get('username')
    password = cam_settings.get('password')
    plate_tag = cam_settings.get('plate', 'licensePlate') # Örn: "licensePlate"
    timeout = anpr_config.get('timeout', 10)
    cache_duration = anpr_config.get('cache_duration', 3.0)
    retry_count = anpr_config.get('retry_count', 0)

    # 1. Check Cache
    now = datetime.now()
    if target_key in _PLATE_CACHE:
        cached = _PLATE_CACHE[target_key]
        delta = (now - cached['timestamp']).total_seconds()
        if delta < cache_duration:
            logger.info(f"Returning cached plate for {target_key}: {cached['plate']} (age: {delta:.1f}s)")
            return cached['plate'], cached['status']

    url = f"http://{server}:{port}{url_path}"
    
    # 2. Fetch with Retries
    attempts = 0
    max_attempts = retry_count + 1
    
    while attempts < max_attempts:
        attempts += 1
        try:
            auth = HTTPDigestAuth(username, password)
            # Konfigüre edilen timeout kullanılıyor
            response = requests.get(url, auth=auth, stream=True, timeout=timeout)
            http_status = response.status_code
            
            xml_content = ""
            # Sadece 200 OK ise içeriği oku
            if http_status == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8', errors='ignore')
                        xml_content += decoded_line + "\n"
                        if "</EventNotificationAlert>" in decoded_line or "</ResponseStatus>" in decoded_line:
                            break
                    if len(xml_content) > 30000: 
                        break
            else:
                xml_content = response.text
            
            if xml_content:
                log_anpr_xml(target_key, xml_content, http_status)
                if http_status != 200:
                    # If it's a transient error, retry
                    if attempts < max_attempts: continue
                    return "ANPR_ERROR", http_status
                
                if "<ResponseStatus" in xml_content:
                    if attempts < max_attempts: continue
                    return "ANPR_ERROR", http_status

                
                plate = parse_plate_from_xml(xml_content, plate_tag)
                
                # If NO_PLATE, maybe retry?
                if plate == "NO_PLATE" and attempts < max_attempts:
                    logger.info(f"Attempt {attempts}: No plate found, retrying...")
                    continue

                # Update Cache
                _PLATE_CACHE[target_key] = {
                    'plate': plate,
                    'status': http_status,
                    'timestamp': now
                }
                return plate, http_status
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout connecting to camera {target_key} (Attempt {attempts}/{max_attempts})")
            if attempts < max_attempts: continue
            return "ANPR_ERROR", 408 # Request Timeout
        except Exception as e:
            logger.error(f"Error fetching ANPR XML from {target_key}: {e}")
            if attempts < max_attempts: continue
            return "ANPR_ERROR", 0

    
    return "NO_PLATE", 0


def parse_plate_from_xml(xml_data, plate_tag):
    """
    XML içinden belirtilen etiketi (plate_tag) bulur ve değerini döndürür.
    """
    try:
        # Hikvision XML namespace içerebilir, bu yüzden tag ismine göre arıyoruz
        # Basitlik için tag'i içeren bir arama yapıyoruz
        root = ET.fromstring(xml_data)
        
        # plate_tag içeren elementi ara (örn: licensePlate)
        # Namespace bağımsız arama için:
        for elem in root.iter():
            if plate_tag in elem.tag:
                if elem.text:
                    plate = elem.text.strip()
                    logger.info(f"Parsed Plate: {plate}")
                    return plate
    except Exception as e:
        logger.error(f"XML Parsing error: {e}")
    
    return "NO_PLATE"

def log_anpr_xml(camera, xml_data, http_status=200):
    """
    Gelen XML verisini anpr_requests.log dosyasına yazar.
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"\n{'='*50}\nTIMESTAMP: {timestamp}\nCAMERA: {camera}\nHTTP STATUS: {http_status}\n{'='*50}\n{xml_data}\n"
        
        with open("anpr_requests.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Failed to write ANPR XML to log: {e}")

def test_camera(cam_settings):
    """
    Connects to the camera and returns (raw_xml, status_code, parsed_plate) for testing.
    """
    server = cam_settings.get('server')
    port = cam_settings.get('port', 80)
    url_path = cam_settings.get('URL', '/ISAPI/Event/notification/alertStream')
    username = cam_settings.get('username')
    password = cam_settings.get('password')
    plate_tag = cam_settings.get('plate', 'licensePlate')
    timeout = cam_settings.get('timeout', 10) # default to 10 if not provided

    url = f"http://{server}:{port}{url_path}"
    
    try:
        auth = HTTPDigestAuth(username, password)
        # Dynamic timeout used for testing
        response = requests.get(url, auth=auth, stream=True, timeout=timeout)
        http_status = response.status_code
        
        xml_content = ""
        if http_status == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8', errors='ignore')
                    xml_content += decoded_line + "\n"
                    if "</EventNotificationAlert>" in decoded_line or "</ResponseStatus>" in decoded_line:
                        break
                if len(xml_content) > 30000: 
                    break
        else:
            xml_content = response.text
        
        # Parse plate if it's 200 OK and not a ResponseStatus error
        parsed_plate = "N/A"
        if http_status == 200 and "<ResponseStatus" not in xml_content:
            parsed_plate = parse_plate_from_xml(xml_content, plate_tag)
        elif "<ResponseStatus" in xml_content:
            parsed_plate = "CAM_ERROR"

        return xml_content, http_status, parsed_plate
            
    except requests.exceptions.Timeout:
        return "TIMEOUT: Camera did not send any data within 10 seconds. Is a car passing or is ANPR enabled?", 408, "TIMEOUT"
    except Exception as e:
        return str(e), 0, "ERROR"
