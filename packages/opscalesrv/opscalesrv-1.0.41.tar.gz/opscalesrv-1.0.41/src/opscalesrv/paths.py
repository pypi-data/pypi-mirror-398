import os
import sys

def get_home_dir():
    """Returns the user's home directory."""
    return os.path.expanduser("~")

def get_marker_file():
    """Returns the path to the hidden file storing the workspace location."""
    return os.path.join(get_home_dir(), ".opscalesrv_path")

def get_base_path():
    """
    Returns the path where configuration, license and logs are stored.
    Checks for a .opscalesrv_path file in home directory.
    """
    marker = get_marker_file()
    if os.path.exists(marker):
        try:
            with open(marker, 'r', encoding='utf-8') as f:
                path = f.read().strip()
                if path and os.path.exists(path):
                    return path
        except:
            pass
    
    # Fallback to current directory if no path is set yet (e.g. CLI mode)
    return os.getcwd()

def is_path_setup():
    """Checks if the workspace path has been established."""
    marker = get_marker_file()
    if not os.path.exists(marker):
        return False
    try:
        with open(marker, 'r', encoding='utf-8') as f:
            path = f.read().strip()
            return os.path.exists(path)
    except:
        return False

def set_base_path(path):
    """
    Saves the selected workspace path.
    """
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            
        marker = get_marker_file()
        with open(marker, 'w', encoding='utf-8') as f:
            f.write(path)
        return True
    except Exception as e:
        print(f"Error setting base path: {e}")
        return False

def get_config_path():
    return os.path.join(get_base_path(), "opscalesrv.json")

def get_license_path():
    return os.path.join(get_base_path(), "license.key")

def get_log_path(filename="requests.log"):
    # If the filename is an absolute path, returns it.
    # Otherwise, joins it with base path.
    if os.path.isabs(filename):
        return filename
    return os.path.join(get_base_path(), filename)
