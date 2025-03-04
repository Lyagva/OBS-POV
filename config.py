import configparser
import os
from threading import Lock, Condition

# Define default configuration
DEFAULT_CONFIG = {
    "OBS": {
        "host": "localhost",
        "port": "4455",
        "password": ""
    },
    "SERVER": {
        "host": "127.0.0.1",
        "port": "5000"
    },
    "Logging": {
        "log_file": "latest.log"
    }
}

CONFIG_FILE = "config.ini"

def create_default_config():
    config = configparser.ConfigParser()
    for section, values in DEFAULT_CONFIG.items():
        config[section] = values
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
    print(f"Default {CONFIG_FILE} created.")

# Check if config.ini exists, create default if not
if not os.path.exists(CONFIG_FILE):
    create_default_config()

# Initialize ConfigParser and read configuration
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# Lock for ensuring thread-safe access to shared resources
lock = Lock()

# Dictionary to store key bindings and associated OBS scenes
setup = {
    "key": [""] * 10,  # Placeholder for key bindings
    "scene": [""] * 10,  # Placeholder for corresponding scene names
}

# Read OBS WebSocket connection details from config.ini
obs_host = config.get("OBS", "host")  # OBS WebSocket server host
obs_port = config.getint("OBS", "port")  # OBS WebSocket server port
obs_password = config.get("OBS", "password")  # OBS WebSocket authentication password

# Read Flask server configuration from config.ini
flask_host = config.get("SERVER", "host")  # Flask server host
flask_port = config.get("SERVER", "port")  # Flask server port

# Read logging configuration
log_file = config.get("Logging", "log_file")  # Path to log file
log_condition = Condition(lock)  # Condition variable for log updates
key_log = {}  # Dictionary to store the latest key logging data