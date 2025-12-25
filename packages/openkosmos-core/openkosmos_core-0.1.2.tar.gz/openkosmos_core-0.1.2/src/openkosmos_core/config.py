import json
import os

import yaml


class Config:
    config = {}

    def __init__(self, config_file=None):
        self.load(config_file)

    def load(self, config_file=None):
        c_file = config_file
        if c_file is None:
            c_file = os.getenv("KOSMOS_CONFIG", default="config.yml")
        with open(c_file, "r", encoding="utf-8") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
            return self.config

    def get(self, name: str | list[str], config_type=None):
        last = None
        if type(name) is str:
            last = self.config.get(name)
        else:
            last = self.config
            for n in name:
                last = last.get(n)

        if config_type is None:
            return last
        else:
            return config_type(**last)

    def __str__(self):
        return json.dumps(self.config, indent=3, ensure_ascii=False)
