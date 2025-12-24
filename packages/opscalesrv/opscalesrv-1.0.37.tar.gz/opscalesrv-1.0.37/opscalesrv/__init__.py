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


# Import ANPR module
try:
    from . import anpr
    ANPR_MODULE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ANPR module not available: {e}")
    ANPR_MODULE_AVAILABLE = False
    anpr = None

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
ENCODING = "utf-8"
TEST_MODE = False
ON_REQUEST_CALLBACK = None
ON_START_CALLBACK = None

HTTP_SERVER = None
CONFIG = {}

def load_opscalesrv_config():
    """
    Load configuration from opscalesrv.json
    """
    global ALLOWED_HOSTS, LOG_FILE, SERIAL_CONFIG, ENCODING, ANPR_CONFIG, ENABLE_LOGGING, CONFIG
    
    # Try to find config file in current directory first, then in package directory
    config_paths = ['opscalesrv.json', os.path.join(os.path.dirname(__file__), 'opscalesrv.json')]
    
    for config_path in config_paths:
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                ALLOWED_HOSTS = config.get('allowed_hosts', [])
                settings = config.get('settings', {})
                LOG_FILE = settings.get('log_file', 'requests.log')
                ENABLE_LOGGING = settings.get('log_all_requests', False)
                SERIAL_CONFIG = config.get('serial', {})
                ANPR_CONFIG = config.get('anpr', {})
                ENCODING = settings.get('encode', 'utf-8')
                CONFIG = config
                logger.info(f"Loaded {len(ALLOWED_HOSTS)} allowed hosts from {config_path}")
                logger.info(f"Serial config: {SERIAL_CONFIG}")
                logger.info(f"Encoding: {ENCODING}")
                return
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing {config_path}: {e}")
            continue
    
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

def read_serial_data():
    """
    Read data from serial port with full pyserial parameter support
    """
    try:
        if not SERIAL_CONFIG:
            raise Exception("Serial configuration not found in opscalesrv.json")
        
        if not SERIAL_CONFIG.get('enabled', True):
            return 0, "Serial reading is disabled in settings"


        
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
                    return value, "Serial Value"
                except ValueError as e:
                    logger.info(f"Could not convert to float, returning as string: '{data}' (ValueError: {e})")
                    return data, "Serial Value"
            else:
                logger.warning("No data received from serial port (empty string)")
                raise Exception("No data received from serial port")
                
    except serial.SerialException as e:
        logger.error(f"Serial port error: {e}")
        logger.error(f"Port: {port}, Baudrate: {baudrate}, Bytesize: {bytesize}")
        raise e
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {e}")
        logger.error(f"Raw data that failed to decode: {raw_data}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected serial read error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        raise e

def get_test_response(path=None):
    """
    Get test mode response
    """
    plate = "35COD238"
    anpr_enabled = ANPR_CONFIG.get('enabled', False)
    if not anpr_enabled:
        plate = "ANPR_DISABLED"
    else:
        # Check for direction disable even in test mode for consistency
        if path:
            path_lower = path.lower().split('?')[0]
            target_key = None
            if path_lower == '/' or 'entrance' in path_lower:
                target_key = 'entrance'
            elif 'exit' in path_lower:
                target_key = 'exit'
            
            if target_key:
                cam_enabled = ANPR_CONFIG.get(target_key, {}).get('enabled', True)
                if not cam_enabled:
                    plate = "DIRECTION_DISABLED"

        
    return {
        "value": 0,
        "msg": "hello world",
        "mode": "test",
        "result": "OK",
        "plate": plate
    }


def get_serial_response(plate="NO_PLATE"):
    """
    Get serial port response
    """
    try:
        logger.info("Starting serial data read operation")
        value, msg = read_serial_data()
        result = "OK"
        if msg == "Serial reading is disabled in settings":
            result = "DISABLED"
            
        logger.info(f"Serial read successful - Value: {value}, Message: {msg}")
        return {
            "value": value,
            "msg": msg,
            "mode": "read",
            "result": result,
            "plate": plate
        }

    except Exception as e:
        logger.error(f"Serial read failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return {
            "value": -1,
            "msg": str(e),
            "mode": "read",
            "result": "FAIL",
            "plate": plate
        }

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
        # Ignore requests for paths other than /, /entrance, /exit
        # Check base path excluding query parameters
        path_check = self.path.split('?')[0].lower()
        if path_check != '/' and not path_check.startswith('/entrance') and not path_check.startswith('/exit'):
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
                ON_START_CALLBACK(client_ip, self.path)
            except: pass

        
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

        # 1. Get Response Data based on path and mode
        if TEST_MODE or force_test_mode:
            logger.info("Using test mode response")
            message_data = get_test_response(self.path)
            license_plate = message_data.get('plate', "35COD238")
        else:
            is_anpr_path = ('/entrance' in path_check or '/exit' in path_check)
            parallel_enabled = ANPR_CONFIG.get('parallel_read', True)
            force_read = ANPR_CONFIG.get('force_read', False)
            
            if is_anpr_path and ANPR_MODULE_AVAILABLE and parallel_enabled:
                logger.info(f"Using PARALLEL mode for path: {self.path}")
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    # Start both tasks
                    serial_future = executor.submit(get_serial_response, plate="NO_PLATE")
                    anpr_future = executor.submit(anpr.fetch_and_log_xml, self.path, CONFIG)
                    
                    # Wait for serial first as it's usually faster
                    message_data = serial_future.result()
                    serial_ok = (message_data.get('result') == 'OK')
                    
                    if serial_ok or force_read:
                        # Wait for ANPR
                        license_plate, cam_status = anpr_future.result()
                        message_data['plate'] = license_plate
                    else:
                        logger.warning("Serial failed and force_read is false, ignoring ANPR result")
                        # We don't wait for anpr_future specifically here, but ThreadPoolExecutor 
                        # 'with' block will wait for it to finish in background.
            else:
                # Sequential or root path
                logger.info(f"Using SEQUENTIAL mode for path: {self.path}")
                message_data = get_serial_response(plate="NO_PLATE")
                serial_ok = (message_data.get('result') == 'OK')
                
                if is_anpr_path and ANPR_MODULE_AVAILABLE and (serial_ok or force_read):
                    try:
                        license_plate, cam_status = anpr.fetch_and_log_xml(self.path, CONFIG)
                        message_data['plate'] = license_plate
                    except Exception as e:
                        logger.error(f"ANPR trigger error: {e}")
                else:
                    if not is_anpr_path:
                        logger.info("Root path - skipping ANPR")
                    elif not (serial_ok or force_read):
                        logger.warning("Serial failed - skipping ANPR fetch")


        
        logger.info(f"Response data: {message_data}")
        
        # Notify GUI about the received data
        # Notify GUI about the received data (as an intermediate step if needed)
        # But we will rely more on the log_request call at the end
        if ON_REQUEST_CALLBACK:
            try:
                ON_REQUEST_CALLBACK({
                    'client_ip': client_ip,
                    'path': self.path,
                    'response_data': message_data,
                    'status': 'PROCESSING'
                })
            except Exception as e:
                logger.error(f"Callback error: {e}")

        
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
        
        logger.info("Response sent successfully")
    
    def do_POST(self):
        """
        Handle POST requests - Not supported, only GET is allowed
        """
        logger.info(f"POST request from {self.client_address[0]}:{self.client_address[1]} - Method not allowed")
        
        # Send 405 Method Not Allowed response
        self.send_response(405)
        self.send_header('Content-type', 'application/json')
        self.send_header('Allow', 'GET')
        self.end_headers()
        
        # Send error response
        error_response = {
            'error': 'Method Not Allowed',
            'message': 'Only GET method is supported',
            'allowed_methods': ['GET'],
            'timestamp': datetime.now().isoformat()
        }
        
        response_json = json.dumps(error_response, indent=2)
        response_bytes = response_json.encode('utf-8')
        self.wfile.write(response_bytes)
        
        # Log request
        log_request(self.client_address[0], self.client_address[1], 'POST', self.path, 'REJECTED', len(response_bytes), self.headers.get('User-Agent', ''), error_response)
        
        logger.info("POST method rejected - only GET is allowed")
    
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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
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
        
        # Get current working directory
        current_dir = os.getcwd()
        config_dest_path = os.path.join(current_dir, 'opscalesrv.json')
        
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
    global HTTP_SERVER
    
    # Reload config to ensure we have latest settings (especially ANPR)
    load_opscalesrv_config()
    
    try:
        # Ensure we don't start multiple servers on top of each other without cleaning up
        if HTTP_SERVER:
            try:
                HTTP_SERVER.shutdown()
                HTTP_SERVER.server_close()
            except:
                pass

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
    global HTTP_SERVER
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
