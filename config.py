# config.py
from threading import Lock, Condition

# Lock for thread-safe access
lock = Lock()

setup = {"key": [""] * 10, "scene": [""] * 10}

obs_host = "localhost"
obs_port = 4455
obs_password = "12345678"

log_file = "latest.log"
log_condition = Condition(lock)
key_log = {}
