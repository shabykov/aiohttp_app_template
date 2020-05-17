import os
import pathlib
import yaml

BASE_DIR = pathlib.Path(__file__).parent.parent.parent

config_path = os.path.join(BASE_DIR, 'config', 'base.yaml')

def get_config(path):
    with open(path) as f:
        conf = yaml.safe_load(f)
    return conf

config = get_config(config_path)
