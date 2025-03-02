# server.py
import json

import flask
from flask import Flask, render_template, request, Response, jsonify
import obs
import capture
from threading import Thread
import config
import os
import sys
import logging


def get_base_path():
    """Returns the correct base path when running as an .exe"""
    if getattr(sys, 'frozen', False):  # When running as an executable
        return sys._MEIPASS
    return os.path.abspath(".")


app = Flask(__name__, template_folder=os.path.join(get_base_path(), "templates"))

LOG_FILE = config.log_file

# Configure logging to both file and console
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# File handler (appends logs to file)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console handler (prints logs to console)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# Add both handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@app.route('/')
def index():
    return render_template('index.html', scenes=[])


@app.route("/scenes", methods=["GET"])
def scenes():
    return obs.get_scene_list()


@app.route('/post_setup', methods=["POST"])
def post_setup():
    new_setup = {"key": request.json["key"], "scene": request.json["scene"]}

    with config.lock:  # Thread-safe write
        config.setup.clear()
        config.setup.update(new_setup)

    # print(config.setup)
    return ""

@app.route('/get_setup', methods=["GET"])
def get_setup():
    return jsonify(config.setup)


@app.route('/key_log')
def key_log():
    def generate():
        with config.log_condition:
            # Continuously wait for new logs
            while True:
                config.log_condition.wait()  # Remove timeout, only wake when notified

                yield f"data: {json.dumps(config.key_log)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route("/logs", methods=["POST"])
def receive_log():
    try:
        data = request.json
        level = data.get("level", "INFO").upper()
        timestamp = data.get("timestamp", "Unknown Time")
        message = data.get("message", "")

        log_entry = f"[{level}] [{timestamp}] {message}\n"

        # Append log to file
        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        # Also log via Python logging module
        if level == "ERROR":
            logging.error(message)
        elif level == "NOTICE":
            logging.warning(message)  # Flask logging doesn't have NOTICE, so we use WARNING
        elif level == "INFO":
            logging.info(message)
        elif level == "DEBUG":
            logging.debug(message)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Start Flask in a daemon thread
    flask_thread = Thread(target=app.run, kwargs={'debug': False, 'use_reloader': False})
    flask_thread.daemon = True  # Thread exits when main thread exits
    flask_thread.start()

    # Run capture in the main thread
    capture.run()
