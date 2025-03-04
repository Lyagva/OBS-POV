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
    """
    Determine the base path of the application.
    If running as an executable, return the temporary directory.
    Otherwise, return the current working directory.
    """
    if getattr(sys, 'frozen', False):  # When running as an executable
        return sys._MEIPASS
    return os.path.abspath(".")


# Initialize Flask application
app = Flask(__name__, template_folder=os.path.join(get_base_path(), "templates"))

# Configure logging settings
LOG_FILE = config.log_file
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# File handler for logging (appends logs to file)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console handler for logging (prints logs to console)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@app.route('/')
def index():
    """
    Render the main index page.
    """
    return render_template('index.html', scenes=[])


@app.route("/scenes", methods=["GET"])
def scenes():
    """
    Retrieve the list of available scenes from the OBS module.
    """
    return obs.get_scene_list()


@app.route('/post_setup', methods=["POST"])
def post_setup():
    """
    Update the setup configuration with a new key and scene.
    Ensures thread safety using a lock.
    """
    new_setup = {"key": request.json["key"], "scene": request.json["scene"]}
    with config.lock:
        config.setup.clear()
        config.setup.update(new_setup)
    return ""


@app.route('/get_setup', methods=["GET"])
def get_setup():
    """
    Retrieve the current setup configuration.
    """
    return jsonify(config.setup)


@app.route('/key_log')
def key_log():
    """
    Stream key logs to the client using Server-Sent Events (SSE).
    """

    def generate():
        with config.log_condition:
            while True:
                config.log_condition.wait()  # Wait until notified
                yield f"data: {json.dumps(config.key_log)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route("/logs", methods=["POST"])
def receive_log():
    """
    Receive and process log data sent via POST request.
    Logs messages to both file and console based on the specified log level.
    """
    try:
        data = request.json
        level = data.get("level", "INFO").upper()
        timestamp = data.get("timestamp", "Unknown Time")
        message = data.get("message", "")
        log_entry = f"[{level}] [{timestamp}] {message}\n"

        # Append log entry to file
        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        # Log via Python's logging module
        if level == "ERROR":
            logging.error(message)
        elif level == "NOTICE":
            logging.warning(message)  # Flask logging does not support NOTICE level
        elif level == "INFO":
            logging.info(message)
        elif level == "DEBUG":
            logging.debug(message)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    """
    Start the Flask application in a separate daemon thread while running the
    capture module in the main thread.
    """
    flask_thread = Thread(target=app.run, kwargs={'debug': False, 'use_reloader': False})
    flask_thread.daemon = True  # Ensures thread exits when the main program terminates
    flask_thread.start()
    capture.run()
