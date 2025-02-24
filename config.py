# config.py
from threading import Lock, Condition
from datetime import datetime
from collections import deque

# Lock for thread-safe access
scene_lock = Lock()

scenes = {}


obs_host = "localhost"
obs_port = 4455
obs_password = "12345678"

MAX_LOG_HISTORY = 10
log_lock = Lock()
log_history = deque(maxlen=MAX_LOG_HISTORY)
log_condition = Condition(log_lock)