# Python
import yaml
from yaml.loader import SafeLoader
from pathlib import Path

def readFile(file = 'tests.yml'):
    # Locate file
    file_path = Path(__file__).parent.parent / "files" / file

    # open yaml file in read
    with open(file_path, 'r', encoding='utf-8') as f:
        data = list(yaml.load_all(f, Loader=SafeLoader))

    return list(data[0].items())