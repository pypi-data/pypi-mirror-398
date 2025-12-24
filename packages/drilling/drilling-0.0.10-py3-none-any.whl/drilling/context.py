import sys
from pathlib import Path
import ipynbname
import yaml
import shutil
import os

try: 
    paths = Path(ipynbname.path()).parent
    FILE_NAME = Path(ipynbname.path()).name
except: 
    paths = Path(sys.argv[0]).parent
    FILE_NAME = Path(sys.argv[0]).name

ENABLE_CONTEXT = False
try: # Context Locator
    for c in range(10):
        root = paths / "params.yaml" if c == 0 else paths.parents[c-1] / "params.yaml"
        if root.is_file():
            sys.path.append(str(root.parent))
            with open(root, "r", encoding="utf-8") as f: 
                parameters = yaml.safe_load(f); break;
    PARAMS = parameters['Settings']
    ENABLE_CONTEXT = True
except: PARAMS = {}

if ENABLE_CONTEXT:
    BASE_PATH = Path(PARAMS.get('DrdRoot'))
    SOURCE_PATH = BASE_PATH / 'src'
    SOURCE_PATH.mkdir(exist_ok=True)
    DATA_PATH = BASE_PATH / 'production' 
    DATA_PATH.mkdir(exist_ok=True)

CLIENT_NAME = PARAMS.get('ClientContext', 'NotDefined')

