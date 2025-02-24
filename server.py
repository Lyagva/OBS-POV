# server.py
import flask
from flask import Flask, render_template, request, Response
import obs
import capture
from threading import Thread
import config


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', scenes=[], MAX_LOG_HISTORY=config.MAX_LOG_HISTORY)


@app.route("/scenes", methods=["GET"])
def scenes():
    return obs.get_scene_list()


@app.route('/save', methods=["POST"])
def save():
    new_scenes = {}
    for element in request.get_json()["configurations"]:
        new_scenes[element["key"]] = element["scene"]

    with config.scene_lock:  # Thread-safe write
        config.scenes.clear()
        config.scenes.update(new_scenes)

    print(config.scenes)
    return ""


@app.route('/logs')
def logs():
    def generate():
        with config.log_condition:
            # Send all existing logs first
            for entry in list(config.log_history):  # Copy to avoid modification during iteration
                yield f"data: {entry}\n\n"

            # Continuously wait for new logs
            while True:
                config.log_condition.wait()  # Remove timeout, only wake when notified

                # Only send new logs
                while config.log_history:
                    entry = config.log_history.popleft()  # Safely remove logs
                    yield f"data: {entry}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    # Start Flask in a daemon thread
    flask_thread = Thread(target=app.run, kwargs={'debug': False, 'use_reloader': False})
    flask_thread.daemon = True  # Thread exits when main thread exits
    flask_thread.start()

    # Run capture in the main thread
    capture.run()