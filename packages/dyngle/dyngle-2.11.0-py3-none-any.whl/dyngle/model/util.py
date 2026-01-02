import json
import yaml
from pathlib import PurePath


# Set up special representations in yaml

def _yaml_none_as_nothing(dumper, _):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')

def _yaml_path_as_str(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))

yaml.add_representer(type(None), _yaml_none_as_nothing, Dumper=yaml.SafeDumper)
yaml.add_multi_representer(PurePath, _yaml_path_as_str, Dumper=yaml.SafeDumper)


def yamlify(value):
    """Convert a structure to a yaml string or plain string
    """
    if isinstance(value, str):
        result = value
    else:
        result = yaml.safe_dump(value, default_flow_style=False)
    # Remove yaml ending from single values
    if result.endswith('\n...\n'):
        result = result[:-4]
    return result.strip()

def jsonify(value):
    if isinstance(value, (dict, list, set, tuple)):
        result = json.dumps(value, default=str)
    else:
        result = str(value)
    return result.strip()