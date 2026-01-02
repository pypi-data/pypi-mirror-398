#!/usr/bin/env python3
"""
Serial Server HTTP Service that reads from serial port or returns test data
with host-based access control
"""

import http.server
import socketserver
import json
import logging
import os
import serial
import serial.tools.list_ports
import shutil
import threading
import concurrent.futures
from datetime import datetime

from . import paths


# Import ANPR module
try:
    from . import anpr
    ANPR_MODULE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ANPR module not available: {e}")
    ANPR_MODULE_AVAILABLE = False
    anpr = None

# Import ANPR Listener module
try:
    from . import anpr_listener
    ANPR_LISTENER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ANPR Listener module not available: {e}")
    ANPR_LISTENER_AVAILABLE = False
    anpr_listener = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to control logging
ENABLE_LOGGING = False

# Global variables for host control and serial configuration
ALLOWED_HOSTS = {}
LOG_FILE = "requests.log"
SERIAL_CONFIG = {}
ANPR_CONFIG = {}
ANPR_LISTENER_CONFIG = {}
ENCODING = "utf-8"
TEST_MODE = False
ON_REQUEST_CALLBACK = None
ON_START_CALLBACK = None

HTTP_SERVER = None
CONFIG = {}

# Serial status (updated per request)
SERIAL_STATUS = None  # True = OK, False = Error, None = Not started

def load_opscalesrv_config():
    """
    Load configuration from opscalesrv.json
    """
    global ALLOWED_HOSTS, LOG_FILE, SERIAL_CONFIG, ENCODING, ANPR_CONFIG, ANPR_LISTENER_CONFIG, ENABLE_LOGGING, CONFIG
    
    # Use centralized path
    config_path = paths.get_config_path()
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                ALLOWED_HOSTS = config.get('allowed_hosts', [])
                settings = config.get('settings', {})
                LOG_FILE = paths.get_log_path(settings.get('log_file', 'requests.log'))
                ENABLE_LOGGING = settings.get('log_all_requests', False)
                SERIAL_CONFIG = config.get('serial', {})
                ANPR_CONFIG = config.get('query', {})  # Changed from 'anpr' to 'query'
                ANPR_LISTENER_CONFIG = config.get('listener', {})  # Changed from 'anpr_listener' to 'listener'
                ENCODING = settings.get('encode', 'utf-8')
                CONFIG = config
                logger.info(f"Loaded {len(ALLOWED_HOSTS)} allowed hosts from {config_path}")
                logger.info(f"Serial config: {SERIAL_CONFIG}")
                # Log minimal ANPR listener info since it is part of main server now
                logger.info(f"ANPR Listener URL: {ANPR_LISTENER_CONFIG.get('url', 'Not Set')}")
                logger.info(f"Encoding: {ENCODING}")
                return
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
    
    # If no config file found, automatically initialize one
    # Note: In GUI mode, this might be called before GUI setup, 
    # but we will handle the setup in GUI's main().
    if not paths.is_path_setup():
        # Skip auto-creation if path not setup yet
        return
        
    print("\n" + "="*60)
    print("🔧 OpScaleSrv - Configuration File Not Found")
    print("="*60)
    print("❌ No opscalesrv.json configuration file found.")
    print("🔧 Automatically creating configuration file...")
    
    success = init_config_file(interactive=False)
    
    # If no config file found, automatically initialize one
    print("\n" + "="*60)
    print("🔧 OpScaleSrv - Configuration File Not Found")
    print("="*60)
    print("❌ No opscalesrv.json configuration file found in current directory.")
    print("🔧 Automatically creating configuration file...")
    
    success = init_config_file(interactive=False)
    
    if success:
        print("\n" + "="*60)
        print("📋 IMPORTANT: Configuration Required")
        print("="*60)
        print("✅ Configuration file 'opscalesrv.json' has been created successfully!")
        print("")
        print("⚠️  BEFORE STARTING THE SERVER, YOU MUST EDIT THE CONFIGURATION:")
        print("")
        print("1. 📝 Edit opscalesrv.json file:")
        print("   - Set your serial port path (e.g., '/dev/ttyUSB0', 'COM1')")
        print("   - Configure baudrate, bytesize, and other serial parameters")
        print("   - Add allowed host IP addresses and ports")
        print("   - Set encoding if needed (e.g., 'iso-8859-9' for Turkish)")
        print("")
        print("2. 🔧 Required serial parameters:")
        print("   - port: Serial port path (REQUIRED)")
        print("   - baudrate: Communication speed (REQUIRED)")
        print("   - bytesize: Data bits 5,6,7,8 (REQUIRED)")
        print("")
        print("3. 📖 For detailed documentation and examples:")
        print("   🌐 https://pypi.org/project/opscalesrv/")
        print("")
        print("4. 🚀 After editing, restart the server:")
        print("   opscalesrv --host 0.0.0.0 --port 7373")
        print("")
        print("="*60)
        exit(0)
    else:
        print("\n❌ Failed to create configuration file!")
        print("🔧 Please run manually: opscalesrv --init")
        print("📖 Documentation: https://pypi.org/project/opscalesrv/")
        exit(1)

def is_host_allowed(client_ip, port):
    """
    Check if the client IP is allowed to access the specified port
    """
    if not ALLOWED_HOSTS:
        return True  # If no opscalesrv.json, allow all
    
    for host_config in ALLOWED_HOSTS:
        if host_config['ip'] == client_ip and port in host_config['ports']:
            return True
    return False

def log_request(client_ip, client_port, method, path, status, response_size=0, user_agent="", response_data=None):
    """
    Log request to requests.log file with response data (only if logging is enabled)
    """
    # Notify callback if exists
    if ON_REQUEST_CALLBACK:
        try:
            # Pass a dictionary for consistency
            callback_data = {
                'client_ip': client_ip,
                'path': path,
                'response_data': response_data,
                'status': status
            }
            ON_REQUEST_CALLBACK(callback_data)
        except Exception as e:
            logger.error(f"Callback error: {e}")



    # Only log if logging is enabled
    if not ENABLE_LOGGING:
        return
        
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    # Basic log entry
    log_entry = f"{timestamp} | {status} | {client_ip}:{client_port} | {method} {path} | {response_size} bytes | {user_agent}\n"
    
    # Add response data if provided
    if response_data:
        try:
            # Convert response data to JSON string for logging
            response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
            log_entry += f"RESPONSE DATA:\n{response_json}\n"
        except Exception as e:
            log_entry += f"RESPONSE DATA (JSON error): {str(response_data)}\n"
    
    log_entry += "---\n"  # Separator for readability
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")

def read_serial_data_once():
    """
    Read data from serial port once (for monitoring thread)
    Returns: (success: bool, value: float/str, message: str)
    """
    try:
        if not SERIAL_CONFIG:
            raise Exception("Serial configuration not found in opscalesrv.json")
        
        # Check serial enabled from settings
        settings = CONFIG.get('settings', {})
        serial_enabled = settings.get('serial', True)
        if not serial_enabled:
            return False, 0, "Serial reading is disabled in settings"


        
        # Required parameters
        port = SERIAL_CONFIG.get('port')
        baudrate = SERIAL_CONFIG.get('baudrate')
        bytesize = SERIAL_CONFIG.get('bytesize')
        
        if not port:
            raise Exception("Serial port is required in opscalesrv.json")
        if not baudrate:
            raise Exception("Serial baudrate is required in opscalesrv.json")
        if not bytesize:
            raise Exception("Serial bytesize is required in opscalesrv.json")
        
        # Build serial connection parameters
        serial_params = {
            'port': port,
            'baudrate': baudrate,
            'bytesize': bytesize
        }
        
        # Optional parameters - only add if they exist in config
        optional_params = {
            'parity': SERIAL_CONFIG.get('parity'),
            'stopbits': SERIAL_CONFIG.get('stopbits'),
            'timeout': SERIAL_CONFIG.get('timeout'),
            'xonxoff': SERIAL_CONFIG.get('xonxoff'),
            'rtscts': SERIAL_CONFIG.get('rtscts'),
            'dsrdtr': SERIAL_CONFIG.get('dsrdtr'),
            'write_timeout': SERIAL_CONFIG.get('write_timeout'),
            'inter_byte_timeout': SERIAL_CONFIG.get('inter_byte_timeout'),
            'exclusive': SERIAL_CONFIG.get('exclusive')
        }
        
        # Add optional parameters only if they are not None
        for param, value in optional_params.items():
            if value is not None:
                serial_params[param] = value
        
        logger.info(f"Opening serial connection with parameters: {serial_params}")
        
        # Open serial connection
        with serial.Serial(**serial_params) as ser:
            logger.info(f"Serial port {port} opened successfully")
            
            # Read data
            raw_data = ser.readline()
            logger.debug(f"Raw data received: {raw_data}")
            
            # Decode with configured encoding
            try:
                data = raw_data.decode(ENCODING).strip()
                logger.info(f"Decoded data using {ENCODING}: '{data}'")
            except UnicodeDecodeError as e:
                logger.warning(f"Failed to decode with {ENCODING}, falling back to utf-8: {e}")
                try:
                    data = raw_data.decode('utf-8').strip()
                    logger.info(f"Successfully decoded with utf-8: '{data}'")
                except UnicodeDecodeError:
                    logger.warning("Failed to decode with utf-8, using latin-1")
                    data = raw_data.decode('latin-1').strip()
                    logger.info(f"Successfully decoded with latin-1: '{data}'")
            
            if data:
                # Try to convert to float, if fails return as string
                try:
                    value = float(data)
                    logger.info(f"Converted to float value: {value}")
                    return True, value, "Serial Value"
                except ValueError as e:
                    logger.info(f"Could not convert to float, returning as string: '{data}' (ValueError: {e})")
                    return True, data, "Serial Value"
            else:
                logger.warning("No data received from serial port (empty string)")
                return False, 0, "No data received from serial port"
                
    except serial.SerialException as e:
        logger.error(f"Serial port error: {e}")
        logger.error(f"Port: {port}, Baudrate: {baudrate}, Bytesize: {bytesize}")
        return False, 0, str(e)
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {e}")
        logger.error(f"Raw data that failed to decode: {raw_data}")
        return False, 0, f"Unicode decode error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected serial read error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False, 0, f"Error: {str(e)}"

def read_serial_data():
    """
    Read data from serial port with full pyserial parameter support
    (Legacy function for backward compatibility)
    Returns: (value, msg) - if error, value will be 0 and msg will contain error message
    """
    success, value, msg = read_serial_data_once()
    if success:
        return value, msg
    else:
        # Return error indication - value 0 with error message
        return 0, f"Serial Error: {msg}"

def serial_read_thread():
    """
    Thread that reads serial port once per request
    Updates SERIAL_STATUS and then exits
    """
    global SERIAL_STATUS
    
    try:
        # Check if serial is enabled
        settings = CONFIG.get('settings', {})
        serial_enabled = settings.get('serial', True)
        
        if not serial_enabled:
            SERIAL_STATUS = None
            return
        
        # Try to read from serial port (this opens, reads, and closes the port)
        success, value, msg = read_serial_data_once()
        if success:
            SERIAL_STATUS = True
        else:
            SERIAL_STATUS = False
            
    except Exception as e:
        logger.error(f"Error in serial read thread: {e}")
        SERIAL_STATUS = False

def get_test_response(path=None):
    """
    Get test mode response
    """
    plate = "NO_PLATE"
    
    # Check ANPR(ISAPI) mode from settings
    settings = CONFIG.get('settings', {})
    anpr_mode = settings.get('isapi', 'disabled')
    
    # If ANPR(ISAPI) is not disabled, set plate to test value
    if anpr_mode != 'disabled':
        plate = "35ABC123"
    else:
        plate = "ANPR_DISABLED"

        
    return {
        "value": 0,
        "msg": "hello world",
        "mode": "test",
        "result": "OK",
        "plate": plate
    }


def get_serial_response(plate="NO_PLATE", include_plate=False):
    """
    Get serial port response
    include_plate: If True, include 'plate' key in response (for test mode)
    """
    try:
        logger.info("Starting serial data read operation")
        value, msg = read_serial_data()
        
        # Check if reading is disabled
        if msg == "Serial reading is disabled in settings":
            result = "DISABLED"
            logger.info(f"Serial reading disabled - Message: {msg}")
        # Check if read was successful (value is not 0 or msg doesn't contain error keywords)
        elif value == 0 and any(error_keyword in msg.lower() for error_keyword in ['error', 'failed', 'exception', 'timeout', 'no data']):
            result = "FAIL"
            logger.error(f"Serial read failed - Value: {value}, Message: {msg}")
        else:
            result = "OK"
            logger.info(f"Serial read successful - Value: {value}, Message: {msg}")
        
        response = {
            "value": value,
            "msg": msg,
            "mode": "read",
            "result": result
        }
        
        # Only include plate if explicitly requested (for test mode)
        if include_plate:
            response["plate"] = plate
        
        return response

    except Exception as e:
        logger.error(f"Serial read failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        response = {
            "value": -1,
            "msg": str(e),
            "mode": "read",
            "result": "FAIL"
        }
        
        # Only include plate if explicitly requested (for test mode)
        if include_plate:
            response["plate"] = plate
        
        return response

# Configuration will be loaded after all functions are defined

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class SerialServerHandler(http.server.BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for serial server with host-based access control
    """
    
    def check_access(self):
        """
        Check if the client is allowed to access the service
        """
        client_ip = self.client_address[0]
        server_port = self.server.server_address[1]
        user_agent = self.headers.get('User-Agent', '')
        
        # Check if host is allowed
        if is_host_allowed(client_ip, server_port):
            logger.info(f"ACCEPTED: {self.command} request from {client_ip}:{self.client_address[1]} to port {server_port}")
            log_request(client_ip, self.client_address[1], self.command, self.path, "ACCEPTED", 0, user_agent)
            return True
        else:
            logger.warning(f"DENIED: {self.command} request from {client_ip}:{self.client_address[1]} to port {server_port}")
            log_request(client_ip, self.client_address[1], self.command, self.path, "DENIED", 0, user_agent)
            return False
    
    def do_GET(self):
        """
        Handle GET requests
        """
        # Check base path excluding query parameters
        path_check = self.path.split('?')[0].lower()
        
        # Get server URL from config
        server_url = CONFIG.get('settings', {}).get('server_url', '').strip()
        server_url_normalized = server_url.lower().strip('/') if server_url else ''
        
        # Check if this is the configured server URL
        path_normalized = path_check.strip('/')
        is_server_url = server_url_normalized and path_normalized == server_url_normalized
        
        # Allow: /, /entrance, /exit, or configured server_url
        if path_check != '/' and not path_check.startswith('/entrance') and not path_check.startswith('/exit') and not is_server_url:
            return  # Silently ignore invalid paths
        
        # Check access first
        if not self.check_access():
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Access Denied')
            return
        
        # Define client_ip for callbacks
        client_ip = self.client_address[0]
        
        if ON_START_CALLBACK:
            try:
                logger.info(f"Calling ON_START_CALLBACK with client_ip={client_ip}, path={self.path}")
                ON_START_CALLBACK(client_ip, self.path)
                logger.info("ON_START_CALLBACK completed successfully")
            except Exception as e:
                logger.error(f"ON_START_CALLBACK error: {e}", exc_info=True)

        
        logger.info(f"GET request from {client_ip}:{self.client_address[1]}")

        logger.info(f"Request path: {self.path}")
        
        # Check for test parameter in URL
        force_test_mode = False
        if '?test=1' in self.path or '&test=1' in self.path:
            force_test_mode = True
            logger.info("Test mode requested via URL parameter")
        
        # License plate and camera status
        license_plate = "NO_PLATE"
        cam_status = 0
        message_data = {}
        anpr_plate_tag = None
        listener_plate_tag = None
        
        # Initialize plates dictionary (used in both test and normal mode)
        # Only one mode (query or listener) can be active at a time
        plates = {}  # {response_tag: plate}

        # 1. Get Response Data based on path and mode
        if TEST_MODE or force_test_mode:
            logger.info("Using test mode response")
            message_data = get_test_response(self.path)
            license_plate = message_data.get('plate', "35ABC123")
        else:
            is_anpr_path = ('/entrance' in path_check or '/exit' in path_check)
            parallel_enabled = ANPR_CONFIG.get('parallel_read', True)
            force_read = ANPR_CONFIG.get('force_read', False)
            
            # Check ANPR mode - only one can be active (query or listener)
            # Get isapi mode from settings
            settings = CONFIG.get('settings', {})
            anpr_mode = settings.get('isapi', 'disabled')
            
            # Get serial response (always needed)
            # Start a thread to read serial port for this request
            settings = CONFIG.get('settings', {})
            serial_enabled = settings.get('serial', True)
            
            if serial_enabled:
                # Start thread to read serial port (opens, reads, and closes)
                serial_thread = threading.Thread(target=serial_read_thread, daemon=True)
                serial_thread.start()
                # Wait for thread to complete (with timeout)
                serial_thread.join(timeout=5.0)  # Wait max 5 seconds
            
            # Now read the serial data (don't include plate in normal mode)
            message_data = get_serial_response(plate="NO_PLATE", include_plate=False)
            serial_ok = (message_data.get('result') == 'OK')
            
            if anpr_mode == 'listen':
                # Listener mode - collect all enabled listener plates
                if ANPR_LISTENER_AVAILABLE:
                    listeners = ANPR_LISTENER_CONFIG.get('listeners', [])
                    all_listener_data = anpr_listener.get_all_listener_plates()
                    
                    for listener in listeners:
                        if listener.get('enabled', True):
                            listener_url = listener.get('url', '').rstrip('/')
                            response_tag = listener.get('response_tag', '').strip()
                            
                            if response_tag and listener_url:
                                # Get timeout for this listener (default 60 seconds)
                                timeout_seconds = listener.get('timeout_seconds', 60)
                                
                                listener_data = all_listener_data.get(listener_url)
                                if listener_data and listener_data.get('plate') and listener_data.get('captured_at'):
                                    # Check freshness: captured within timeout window
                                    delta = (datetime.now() - listener_data['captured_at']).total_seconds()
                                    if delta < timeout_seconds:
                                        plates[response_tag] = listener_data['plate']
                                        logger.info(f"Using plate from Listener '{listener.get('name', listener_url)}': {listener_data['plate']} (Response Tag: {response_tag}, Age: {delta:.1f}s, Timeout: {timeout_seconds}s)")
                                    else:
                                        # Timeout exceeded - return NO_PLATE
                                        plates[response_tag] = "NO_PLATE"
                                        logger.warning(f"Listener '{listener.get('name', listener_url)}' timeout exceeded (Age: {delta:.1f}s > Timeout: {timeout_seconds}s) - returning NO_PLATE")
                                else:
                                    # No data received yet or no plate - return NO_PLATE
                                    plates[response_tag] = "NO_PLATE"
                                    logger.warning(f"Listener '{listener.get('name', listener_url)}' has no plate data - returning NO_PLATE")
            
            elif anpr_mode == 'query':
                # Query mode - fetch from all enabled cameras
                if ANPR_MODULE_AVAILABLE:
                    # Get all enabled cameras from config
                    cameras = ANPR_CONFIG.get('cameras', [])
                    enabled_cameras = [cam for cam in cameras if cam.get('enabled', True)]
                    
                    if enabled_cameras:
                        logger.info(f"Query mode: Fetching from {len(enabled_cameras)} enabled camera(s)")
                        
                        # Start threads for each enabled camera
                        camera_futures = {}
                        with concurrent.futures.ThreadPoolExecutor(max_workers=len(enabled_cameras)) as executor:
                            for camera in enabled_cameras:
                                camera_name = camera.get('name', 'Unknown')
                                response_tag = camera.get('response_tag', '').strip()
                                
                                if response_tag:  # Only fetch if response_tag is set
                                    # Submit camera fetch task
                                    future = executor.submit(anpr.fetch_from_camera, camera, ANPR_CONFIG, camera_name)
                                    camera_futures[response_tag] = future
                                    logger.info(f"Started thread for camera '{camera_name}' (Response Tag: {response_tag})")
                            
                            # Wait for all camera threads to complete
                            for response_tag, future in camera_futures.items():
                                try:
                                    license_plate, cam_status, plate_tag = future.result(timeout=ANPR_CONFIG.get('timeout', 10) + 5)
                                    # Define error codes
                                    error_codes = ["ANPR_ERROR", "CAM_ERROR", "CAM_TIMEOUT", "CAM_CONNECTION_ERROR", "ERROR", "TIMEOUT"]
                                    
                                    # Always add to plates dictionary (both valid plates and errors)
                                    if license_plate:
                                        if license_plate in error_codes:
                                            # It's an error code - add it to plates
                                            plates[response_tag] = license_plate
                                            logger.warning(f"Camera '{response_tag}' returned error: {license_plate}")
                                        elif license_plate == "NO_PLATE":
                                            # NO_PLATE is not an error, just no plate found
                                            plates[response_tag] = "NO_PLATE"
                                            logger.info(f"Camera '{response_tag}' returned NO_PLATE")
                                        else:
                                            # Valid plate
                                            plates[response_tag] = license_plate
                                            logger.info(f"Camera '{response_tag}' returned plate: {license_plate}")
                                    else:
                                        # Empty response - treat as error
                                        plates[response_tag] = "CAM_ERROR"
                                        logger.warning(f"Camera '{response_tag}' returned empty response")
                                except concurrent.futures.TimeoutError:
                                    logger.warning(f"Camera '{response_tag}' thread timed out")
                                    # Add timeout error to plates so it's visible in response
                                    plates[response_tag] = "CAM_TIMEOUT"
                                except Exception as e:
                                    logger.error(f"Error fetching from camera '{response_tag}': {e}")
                                    # Add error to plates so it's visible in response
                                    plates[response_tag] = "CAM_ERROR"
                    else:
                        logger.info("Query mode: No enabled cameras found")


        
        logger.info(f"Response data: {message_data}")
        
        # Add plates to message_data using their response_tags
        for response_tag, plate in plates.items():
            if response_tag:  # Only add if response_tag is not empty
                message_data[response_tag] = plate
        
        # Determine ISAPI result based on mode and errors
        settings = CONFIG.get('settings', {})
        anpr_mode = settings.get('isapi', 'disabled')
        isapi_result = "OK"
        
        if anpr_mode == 'disabled':
            isapi_result = "DISABLED"
        elif anpr_mode == 'query':
            # Get all enabled cameras with response_tag
            cameras = ANPR_CONFIG.get('cameras', [])
            enabled_cameras = [cam for cam in cameras if cam.get('enabled', True) and cam.get('response_tag', '').strip()]
            
            if not enabled_cameras:
                # No enabled cameras configured - OK (nothing to check)
                isapi_result = "OK"
                logger.info("Query mode: No enabled cameras configured - isapi_result: OK")
            else:
                # Check for camera errors in plates
                error_codes = ["CAM_ERROR", "CAM_TIMEOUT", "CAM_CONNECTION_ERROR", "ANPR_ERROR", "ERROR", "TIMEOUT"]
                
                # Get all response_tags for enabled cameras
                enabled_response_tags = {cam.get('response_tag', '').strip() for cam in enabled_cameras if cam.get('response_tag', '').strip()}
                
                # Check if any enabled camera returned an error
                has_error = False
                valid_plates_count = 0
                error_count = 0
                
                for response_tag in enabled_response_tags:
                    plate_value = plates.get(response_tag)
                    if plate_value:
                        if plate_value in error_codes:
                            has_error = True
                            error_count += 1
                            logger.warning(f"Query mode: Camera '{response_tag}' returned error: {plate_value}")
                        elif plate_value != "NO_PLATE":
                            valid_plates_count += 1
                            logger.info(f"Query mode: Camera '{response_tag}' returned valid plate: {plate_value}")
                
                # Determine result based on errors
                if has_error:
                    # At least one camera returned an error - FAIL
                    isapi_result = "FAIL"
                    logger.warning(f"Query mode: {error_count} camera(s) returned error(s) - isapi_result: FAIL")
                elif valid_plates_count > 0:
                    # At least one camera returned a valid plate - OK
                    isapi_result = "OK"
                    logger.info(f"Query mode: {valid_plates_count} valid plate(s) received - isapi_result: OK")
                else:
                    # All cameras returned NO_PLATE or no data - this is OK (no vehicle passing)
                    isapi_result = "OK"
                    logger.info(f"Query mode: All cameras returned NO_PLATE (no vehicle passing) - isapi_result: OK")
        elif anpr_mode == 'listen':
            # Check if at least one listener returned a valid plate (not NO_PLATE)
            valid_plates = [plate for plate in plates.values() if plate and plate != "NO_PLATE"]
            if not valid_plates:
                # No valid plates from any listener - FAIL
                isapi_result = "FAIL"
                logger.warning(f"Listener mode: No valid plates received from any listener - isapi_result: FAIL")
            else:
                # At least one listener returned a valid plate - OK
                isapi_result = "OK"
                logger.info(f"Listener mode: {len(valid_plates)} valid plate(s) received - isapi_result: OK")
        else:
            isapi_result = "OK"
        
        # Add isapi_result to message_data
        message_data['isapi_result'] = isapi_result
        
        # Prepare response data
        response_data = {
            'message': message_data,
            'timestamp': datetime.now().isoformat(),
            'method': 'GET',
            'path': self.path,
            'client_ip': self.client_address[0],
            'client_port': self.client_address[1],
            'cam_status': cam_status
        }
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Send JSON response
        response_json = json.dumps(response_data, indent=2)
        response_bytes = response_json.encode('utf-8')
        self.wfile.write(response_bytes)
        
        # Log successful response with response data
        log_request(self.client_address[0], self.client_address[1], 'GET', self.path, 'ACCEPTED', len(response_bytes), self.headers.get('User-Agent', ''), response_data)
        
        # Notify GUI about the completed request (after response is sent)
        if ON_REQUEST_CALLBACK:
            try:
                ON_REQUEST_CALLBACK({
                    'client_ip': client_ip,
                    'path': self.path,
                    'response_data': response_data,
                    'status': 'COMPLETED'
                })
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info("Response sent successfully")
    
    def do_POST(self):
        """
        Handle POST requests.
        - If path matches ANPR listener URL, process XML.
        - Otherwise, reject.
        """
        # Check if this is an ANPR Listener request
        # Support both old format (single url) and new format (listeners list)
        request_path = self.path.split('?')[0].rstrip('/')
        
        # Try new format first (listeners list)
        matched_listener = None
        listeners = ANPR_LISTENER_CONFIG.get('listeners', [])
        for listener in listeners:
            if listener.get('enabled', True):
                listener_url = listener.get('url', '').rstrip('/')
                if listener_url and request_path == listener_url:
                    matched_listener = listener
                    break
        
        # Fallback to old format
        if not matched_listener:
            listener_url = ANPR_LISTENER_CONFIG.get('url', '').rstrip('/')
            if listener_url and request_path == listener_url:
                # Use old config as listener config
                matched_listener = ANPR_LISTENER_CONFIG
        
        if matched_listener:
             try:
                # Check access (optional, maybe allow 0.0.0.0 or specific IPs)
                # But cameras push from external IPs.
                # If we want to restrict, we should add IPs to ALLOWED_HOSTS for the camera IP.
                if not self.check_access():
                    self.send_response(403)
                    self.end_headers()
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                raw_data = self.rfile.read(content_length)
                
                # Multipart Parsing logic
                content_type = self.headers.get('Content-Type', '')
                xml_content = None
                
                if 'multipart/form-data' in content_type:
                    try:
                        import email.parser
                        from io import BytesIO
                        
                        # Create pseudo-header for email parser
                        headers = f"Content-Type: {content_type}\n"
                        msg = email.parser.BytesParser().parsebytes(headers.encode() + b"\n" + raw_data)
                        
                        save_dir = matched_listener.get('picture_path')
                        if save_dir and not os.path.exists(save_dir):
                            os.makedirs(save_dir, exist_ok=True)

                        for part in msg.get_payload():
                            if not part.is_multipart():
                                part_filename = part.get_filename()
                                part_ctype = part.get_content_type()
                                part_payload = part.get_payload(decode=True)
                                
                                if not part_payload: continue

                                # Identify XML
                                if 'xml' in part_ctype or (part_filename and part_filename.endswith('.xml')):
                                    xml_content = part_payload.decode('utf-8', errors='ignore')
                                    logger.info(f"Extracted XML from multipart: {len(xml_content)} chars")
                                    # Still log it for reference
                                    logger.info(f"ANPR XML Content:\n{xml_content}")
                                
                                # Identify Images
                                elif 'image' in part_ctype or (part_filename and part_filename.lower().endswith(('.jpg', '.jpeg', '.png'))):
                                     if save_dir:
                                         # Generate unique name using timestamp + filename
                                         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                         clean_name = part_filename or "unknown.jpg"
                                         final_path = os.path.join(save_dir, f"{timestamp}_{clean_name}")
                                         with open(final_path, 'wb') as f:
                                             f.write(part_payload)
                                         logger.info(f"Saved ANPR image: {final_path}")
                    except Exception as e:
                        logger.error(f"Error parsing multipart data: {e}")
                        # Fallback: try finding XML in raw decoded data if multipart parse failed
                        if not xml_content:
                             xml_content = raw_data.decode('utf-8', errors='ignore')

                else:
                    # Regular non-multipart post
                    xml_content = raw_data.decode('utf-8', errors='ignore')
                    logger.info(f"ANPR POST Content:\n{xml_content}")

                # Process the XML
                if ANPR_LISTENER_AVAILABLE and xml_content:
                    listener_url = matched_listener.get('url', '').rstrip('/')
                    anpr_listener.process_anpr_xml(xml_content, matched_listener, listener_url)
                
                # Send OK response
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b"OK")
                
                log_request(self.client_address[0], self.client_address[1], 'POST', self.path, 'ANPR_RECEIVED', content_length, self.headers.get('User-Agent', ''))
                
             except Exception as e:
                logger.error(f"Error processing ANPR listener POST request: {e}")
                self.send_response(500)
                self.end_headers()
             return

        logger.info(f"POST request from {self.client_address[0]}:{self.client_address[1]} - Method not allowed (Request: '{request_path}' vs Config: '{config_url}')")
        
        # Send 405 Method Not Allowed response
        self.send_response(405)
        self.send_header('Content-type', 'application/json')
        self.send_header('Allow', 'GET, POST')
        self.end_headers()
        
        # Send error response
        error_response = {
            'error': 'Method Not Allowed',
            'message': 'Only GET method is supported (except configured ANPR URL)',
            'allowed_methods': ['GET'],
            'timestamp': datetime.now().isoformat()
        }
        
        response_json = json.dumps(error_response, indent=2)
        response_bytes = response_json.encode('utf-8')
        self.wfile.write(response_bytes)
        
        # Log request
        log_request(self.client_address[0], self.client_address[1], 'POST', self.path, 'REJECTED', len(response_bytes), self.headers.get('User-Agent', ''), error_response)
        
        logger.info("POST method rejected")
    
    def do_OPTIONS(self):
        """
        Handle OPTIONS requests for CORS
        """
        # Check access first
        if not self.check_access():
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Access Denied')
            return
        
        logger.info(f"OPTIONS request from {self.client_address[0]}:{self.client_address[1]}")
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Log successful response
        log_request(self.client_address[0], self.client_address[1], 'OPTIONS', self.path, 'ACCEPTED', 0, self.headers.get('User-Agent', ''))
    
    def log_message(self, format, *args):
        """
        Override log_message to use our logger
        """
        logger.info(f"{self.address_string()} - {format % args}")

def init_config_file(interactive=True):
    """
    Initialize opscalesrv.json configuration file in current directory
    """
    try:
        # Get package directory
        package_dir = os.path.dirname(__file__)
        config_source_path = os.path.join(package_dir, 'opscalesrv.json')
        
        # Get current data directory
        config_dest_path = paths.get_config_path()
        current_dir = os.path.dirname(config_dest_path)
        
        # Check if source config file exists
        if not os.path.exists(config_source_path):
            logger.error(f"Source config file not found: {config_source_path}")
            return False
        
        # Check if destination file already exists
        if os.path.exists(config_dest_path):
            if interactive:
                print(f"\n⚠️  Configuration file already exists: {config_dest_path}")
                response = input("Do you want to overwrite it? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("❌ Configuration file creation cancelled")
                    return False
            else:
                # In non-interactive mode, overwrite without asking
                logger.info(f"Overwriting existing configuration file: {config_dest_path}")
        
        # Copy the configuration file
        try:
            shutil.copy2(config_source_path, config_dest_path)
            logger.info(f"Copied opscalesrv.json to {current_dir}")
            
            if interactive:
                print(f"\n✅ Successfully created configuration file:")
                print(f"   📄 opscalesrv.json")
                print(f"\n📁 Current directory: {current_dir}")
                print("💡 You can now edit opscalesrv.json to configure your server")
                print("🔧 Available settings:")
                print("   - allowed_hosts: IP addresses and ports")
                print("   - serial: Serial port configuration")
                print("   - settings: Log file and other options")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy configuration file: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing configuration file: {e}")
        return False

def copy_abap_files():
    """
    Copy ABAP files from both package and root abap directories to current directory
    """
    try:
        # Get package directory and root directory
        package_dir = os.path.dirname(__file__)
        root_dir = os.path.dirname(package_dir)
        
        # Define ABAP source directories
        abap_dirs = [
            os.path.join(package_dir, 'abap'),  # opscalesrv/abap/
            os.path.join(root_dir, 'abap')      # abap/
        ]
        
        # Get current working directory
        current_dir = os.getcwd()
        
        # Collect all ABAP files from both directories
        all_abap_files = []
        for abap_dir in abap_dirs:
            if os.path.exists(abap_dir):
                abap_files = [f for f in os.listdir(abap_dir) if f.endswith('.abap')]
                for abap_file in abap_files:
                    source_path = os.path.join(abap_dir, abap_file)
                    all_abap_files.append((abap_file, source_path, abap_dir))
                logger.info(f"Found {len(abap_files)} ABAP files in {abap_dir}")
            else:
                logger.debug(f"ABAP directory not found: {abap_dir}")
        
        if not all_abap_files:
            logger.warning("No ABAP files found in any directory")
            return False
        
        # Copy each ABAP file
        copied_files = []
        skipped_files = []
        
        for abap_file, source_path, source_dir in all_abap_files:
            dest_path = os.path.join(current_dir, abap_file)
            
            # Check if file already exists in destination
            if os.path.exists(dest_path):
                # Compare file sizes to decide whether to skip
                source_size = os.path.getsize(source_path)
                dest_size = os.path.getsize(dest_path)
                
                if source_size == dest_size:
                    logger.info(f"Skipping {abap_file} (already exists with same size)")
                    skipped_files.append(abap_file)
                    continue
            
            try:
                shutil.copy2(source_path, dest_path)
                copied_files.append(abap_file)
                logger.info(f"Copied {abap_file} from {source_dir} to {current_dir}")
            except Exception as e:
                logger.error(f"Failed to copy {abap_file}: {e}")
        
        # Display results
        if copied_files or skipped_files:
            print(f"\n✅ ABAP file copy operation completed:")
            
            if copied_files:
                print(f"   📄 Copied {len(copied_files)} file(s):")
                for file in copied_files:
                    print(f"      ✅ {file}")
            
            if skipped_files:
                print(f"   ⏭️  Skipped {len(skipped_files)} file(s) (already exist):")
                for file in skipped_files:
                    print(f"      ⏭️  {file}")
            
            print(f"\n📁 Current directory: {current_dir}")
            print("💡 You can now copy these files to your SAP system")
            return True
        else:
            logger.error("No ABAP files were copied")
            return False
            
    except Exception as e:
        logger.error(f"Error copying ABAP files: {e}")
        return False

def start_server(port=7373, host='localhost'):
    """
    Start the HTTP server on specified port with host-based access control
    """
    global HTTP_SERVER, SERIAL_STATUS
    
    # Reload config to ensure we have latest settings (especially ANPR)
    load_opscalesrv_config()
    
    # Initialize SERIAL_STATUS
    SERIAL_STATUS = None
    
    try:
        # Ensure we don't start multiple servers on top of each other without cleaning up
        if HTTP_SERVER:
            try:
                HTTP_SERVER.shutdown()
                HTTP_SERVER.server_close()
            except:
                pass
        
        # Start ANPR Listener integration
        # No longer a separate thread or port, handled in do_POST of main server
        # We just log the configuration status
        if ANPR_LISTENER_AVAILABLE and ANPR_LISTENER_CONFIG.get('url'):
            url = ANPR_LISTENER_CONFIG.get('url')
            logger.info(f"ANPR Listener active on main server (POST {url})")

        with ReusableTCPServer((host, port), SerialServerHandler) as httpd:
            HTTP_SERVER = httpd
            logger.info(f"Serial Server starting on {host}:{port}")
            logger.info("Available endpoints:")
            logger.info(f"  GET  http://{host}:{port}/")
#            logger.info(f"  POST http://{host}:{port}/")
            logger.info(f"Host access control: {'ENABLED' if ALLOWED_HOSTS else 'DISABLED'}")
            logger.info(f"Logging: {'ENABLED' if ENABLE_LOGGING else 'DISABLED'}")
            if ENABLE_LOGGING:
                logger.info(f"Log file: {LOG_FILE}")
            logger.info(f"Mode: {'TEST' if TEST_MODE else 'SERIAL'}")
            if not TEST_MODE and SERIAL_CONFIG:
                logger.info(f"Serial port: {SERIAL_CONFIG.get('port', 'Not configured')}")
            logger.info("Press Ctrl+C to stop the server")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {port} is already in use. Please choose a different port.")
        else:
            logger.error(f"Error starting server: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def stop_server():
    """
    Stop the running HTTP server
    """
    global HTTP_SERVER, SERIAL_STATUS
    
    # Reset serial status
    SERIAL_STATUS = None
    
    if HTTP_SERVER:
        logger.info("Stopping Serial Server...")
        threading.Thread(target=HTTP_SERVER.shutdown).start()
        # We don't close here because 'with' block in start_server will handle it



def main():
    """
    Main function - Now launches GUI by default
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='OpScaleSrv - Serial Port Reader HTTP Service')
    parser.add_argument('--cli', action='store_true', help='Run in legacy CLI mode (no GUI)')
    parser.add_argument('--port', type=int, default=7373, help='Port to listen on (CLI mode only)')
    parser.add_argument('--host', default='localhost', help='Host to bind to (CLI mode only)')
    parser.add_argument('--test', action='store_true', help='Run in test mode (CLI mode only)')
    parser.add_argument('--abap', action='store_true', help='Copy ABAP files to current directory and exit')
    parser.add_argument('--init', action='store_true', help='Initialize opscalesrv.json configuration file and exit')
    
    args, unknown = parser.parse_known_args()

    # Handle ABAP file copying or Init if called directly
    if args.abap:
        print("🔧 OpScaleSrv - ABAP File Extractor")
        copy_abap_files()
        return
    if args.init:
        print("🔧 OpScaleSrv - Configuration Initializer")
        init_config_file()
        return

    # If --cli flag is used, run the old server logic
    if args.cli:
        print("Starting in CLI mode...")
        global TEST_MODE
        TEST_MODE = args.test
        start_server(port=args.port, host=args.host)
        return

    # Default: Run the GUI
    try:
        from .gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        print("Falling back to CLI mode...")
        start_server(port=args.port, host=args.host)

# Load configuration on startup (after all functions are defined)
load_opscalesrv_config()

if __name__ == "__main__":
    main()
