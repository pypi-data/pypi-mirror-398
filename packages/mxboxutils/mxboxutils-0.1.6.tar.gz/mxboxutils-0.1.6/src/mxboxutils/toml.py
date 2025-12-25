import tomllib
import os 

def load_toml(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath,"rb") as f:
        return tomllib.load(f)