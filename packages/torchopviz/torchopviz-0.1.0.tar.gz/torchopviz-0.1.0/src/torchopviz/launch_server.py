import threading
import time
import os
from flask import Flask, render_template
import logging
from importlib import resources

from .log import logger
from .comm import package_name


def get_resource_path(package, resource_dir):
    path = resources.files(package).joinpath(resource_dir)
    return str(path)


def launch_visualizer(data, port=5000):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=get_resource_path(package_name, "server/templates"),
        static_folder=get_resource_path(package_name, "server/static"),
    )

    @app.route("/data")
    def get_data():
        return data

    @app.route('/')
    def index():
        return render_template('index.html')

    def run_app():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False,)

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)  # 或 logging.CRITICAL

    # run app in thread
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    # wait 1s
    time.sleep(1)

    url = f"http://localhost:{port}"
    logger.info(f"🌐 visualizer url: {url}")