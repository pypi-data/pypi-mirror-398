try: from drilling.context import *
except: from context import *
import yaml

def ConPrm(name, context=PARAMS['ClientContext']):
    try:
        with open(BASE_PATH / 'src' / f"{context}.yaml", "r") as file:
            data = yaml.safe_load(file)
            data = data["DataSources"][name]
        return data
    except: ValueError(f"Context Source {name} not found in {context}.yaml")