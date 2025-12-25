# coding=utf-8

import os
import yaml
from typing import Any

from addict import Dict


class Configuration:

    def __init__(self):
        self.data = Dict()

    def from_yaml(self, custom_yaml: str):
        default_yaml = os.path.realpath(os.path.join(os.path.dirname(__file__), 'default.yaml'))
        with open(default_yaml, 'r') as fp:
            default_config = yaml.safe_load(fp.read())

        custom_yaml = os.path.realpath(custom_yaml)
        with open(custom_yaml, 'r') as fp:
            custom_config = yaml.safe_load(fp.read())

        self.data.update(Dict(default_config))
        self.data.update(Dict(custom_config))

        workspace = os.path.realpath(os.path.join(os.path.dirname(custom_yaml), os.pardir, os.pardir))
        self.data.project.update(Dict({'workspace': workspace}))

    def get(self, key_path: str):
        obj = self.data
        parts = key_path.split('.')
        for part in parts:
            obj = obj.get(part)
            if obj is None:
                break

        return obj

    def set(self, key_path: str, value: Any):
        parent = None
        obj = self.data
        parts = key_path.split('.')
        for index, part in enumerate(parts):
            parent = obj
            obj = obj.get(part)
            if obj is None and index < len(parts) - 1:
                return

        parent.update({parts[-1]: value})

    def dump(self):
        return self.data.to_dict()

