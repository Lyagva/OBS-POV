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


def get_base_path():
    """Returns the correct base path when running as an .exe"""
    if getattr(sys, 'frozen', False):  # When running as an executable
        return sys._MEIPASS
    return os.path.abspath(".")


app = Flask(__name__, template_folder=os.path.join(get_base_path(), "templates"))


@app.route('/')
def index():
    return render_template('index.html', scenes=[], max_ui_log_history=config.max_ui_log_history)


@app.route("/scenes", methods=["GET"])
def scenes():
    return obs.get_scene_list()


@app.route('/post_setup', methods=["POST"])
def post_setup():
    new_setup = {"key": request.json["key"], "scene": request.json["scene"]}

    with config.lock:  # Thread-safe write
        config.setup.clear()
        config.setup.update(new_setup)

    print(config.setup)
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


if __name__ == '__main__':
    # Start Flask in a daemon thread
    flask_thread = Thread(target=app.run, kwargs={'debug': False, 'use_reloader': False})
    flask_thread.daemon = True  # Thread exits when main thread exits
    flask_thread.start()

    # Run capture in the main thread
    capture.run()
