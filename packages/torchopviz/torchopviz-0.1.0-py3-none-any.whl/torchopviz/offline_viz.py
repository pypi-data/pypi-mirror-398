import time
import argparse

from .launch_server import launch_visualizer
from .utils import load_data
from .log import logger


def offline_viz(file: str):
    json_data = load_data(file)

    launch_visualizer(json_data)
    logger.info(f"visualizer start, stop by Ctrl+C.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("stopped")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="test")
    parser.add_argument("--file", type=str, help="file path", required=True)
    args = parser.parse_args()
    offline_viz(args.file)