import json
import os
from dataclasses import asdict
from pathlib import Path

class LocalStorage(object):
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new LocalStorage instance')
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
        return cls._instance

    cache_dir = os.path.join(
        os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
        "ChtnUniEnd"
    )
    os.makedirs(cache_dir, exist_ok=True)

    @staticmethod
    def write(name, data):
        file_path = os.path.join(LocalStorage.cache_dir, f"{name}.json")
        tmp_path = file_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(asdict(data), f)
        os.replace(tmp_path, file_path)

    @staticmethod
    def read(name):
        file_path = os.path.join(LocalStorage.cache_dir, f"{name}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def get_all():
        resp = []
        for file in Path(LocalStorage.cache_dir).iterdir():
            if file.is_file():
                resp.append((file.name.split(".")[0]))

        return resp