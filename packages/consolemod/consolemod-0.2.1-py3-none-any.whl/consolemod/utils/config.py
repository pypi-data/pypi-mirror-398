import yaml

def load_config(path="console.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")