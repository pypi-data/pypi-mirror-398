import yaml, json
def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f) if path.endswith(("yml","yaml")) else json.load(f)
