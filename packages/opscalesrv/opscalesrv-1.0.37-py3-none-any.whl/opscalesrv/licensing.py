import hashlib
import subprocess
import os
import sys

# Secret salt for hashing - keep this consistent between app and generator
_SECRET_SALT = "OpScale_Industrial_2025_Secure_Salt_v1"

# File name for the license key
_LICENSE_FILE = "license.key"

def get_machine_id():
    """
    Generate a unique hardware ID based on system metadata.
    Supports Windows, Linux, and macOS.
    """
    hid = ""
    try:
        if sys.platform == "win32":
            # Windows: Get Motherboard UUID
            cmd = "wmic csproduct get uuid"
            output = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
            hid = output
        elif sys.platform == "linux":
            # Linux: Try machine-id first
            if os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id", "r") as f:
                    hid = f.read().strip()
            elif os.path.exists("/sys/class/dmi/id/product_uuid"):
                with open("/sys/class/dmi/id/product_uuid", "r") as f:
                    hid = f.read().strip()
            else:
                # Fallback to cpuinfo
                cmd = "cat /proc/cpuinfo | grep Serial | cut -d ':' -f 2"
                hid = subprocess.check_output(cmd, shell=True).decode().strip()
        elif sys.platform == "darwin":
            # macOS: Get IOPlatformUUID
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
            output = subprocess.check_output(cmd, shell=True).decode().split('=')[1].strip().replace('"', '')
            hid = output
    except Exception as e:
        # Final fallback: use hostname if all fails (less secure but prevents crash)
        import socket
        hid = socket.gethostname()

    # Hash the raw HID to a fixed length hex string
    return hashlib.sha256(hid.encode()).hexdigest()[:16].upper()

def generate_key(hid):
    """
    Generate a license key for a given Hardware ID.
    Used by genlicense.py.
    """
    raw = f"{hid}:{_SECRET_SALT}"
    # Use double hash for a bit more obscurity
    h1 = hashlib.sha256(raw.encode()).hexdigest()
    h2 = hashlib.sha256(h1.encode()).hexdigest()
    
    # Format as XXXX-XXXX-XXXX-XXXX
    key = h2.upper()
    parts = [key[i:i+4] for i in range(0, 16, 4)]
    return "-".join(parts)

def get_stored_licenses():
    """Read all license keys from the license.key file as a list"""
    if os.path.exists(_LICENSE_FILE):
        try:
            with open(_LICENSE_FILE, "r") as f:
                # Read all lines, strip whitespace, and filter out empty lines
                return [line.strip() for line in f.readlines() if line.strip()]
        except:
            return []
    return []

def get_stored_license():
    """Backward compatibility: returns the first license key found"""
    licenses = get_stored_licenses()
    return licenses[0] if licenses else None

def save_license(key):
    """
    Append a license key to the license.key file if it doesn't exist.
    """
    try:
        current_licenses = get_stored_licenses()
        key_strip = key.strip().upper()
        
        # If key is already in the file, no need to add again
        if any(lic.upper() == key_strip for lic in current_licenses):
            return True
            
        with open(_LICENSE_FILE, "a") as f:
            # Ensure there is a newline before appending
            if os.path.getsize(_LICENSE_FILE) > 0:
                f.write("\n")
            f.write(key_strip)
        return True
    except:
        return False

def verify_license(stored_key=None):
    """
    Verify if the license is valid for the current machine.
    If stored_key is provided, verify only that key.
    If stored_key is None, check all keys in license.key file.
    """
    current_hid = get_machine_id()
    expected_key = generate_key(current_hid).upper()
    
    if stored_key is not None:
        return stored_key.strip().upper() == expected_key
        
    # Check all stored licenses
    licenses = get_stored_licenses()
    for lic in licenses:
        if lic.strip().upper() == expected_key:
            return True
            
    return False


