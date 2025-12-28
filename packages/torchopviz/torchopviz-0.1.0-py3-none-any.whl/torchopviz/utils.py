import json
import os

from .log import logger


def load_data(file:str):
    logger.info(f"load json file: {os.path.abspath(file)}\n")
    try:
        with open(file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return json_data
    except FileNotFoundError:
        raise FileNotFoundError(f"file not found: {file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"json decode error: {file}\ndetail: {e}")
    except Exception as e:
        raise RuntimeError(f"read file error: {file}\n{e}")