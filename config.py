import configparser
from threading import Lock, Condition

# Initialize ConfigParser
config = configparser.ConfigParser()
config.read("config.ini")

# Lock for thread-safe access
lock = Lock()

# Read setup keys and scenes
setup = {
    "key": [""] * 10,
    "scene": [""] * 10,
}

# Read OBS Configuration
obs_host = config.get("OBS", "host")
obs_port = config.getint("OBS", "port")
obs_password = config.get("OBS", "password")

flask_host = config.get("SERVER", "host")
flask_port = config.get("SERVER", "port")


# Read Logging Configuration
log_file = config.get("Logging", "log_file")
log_condition = Condition(lock)
key_log = {}
