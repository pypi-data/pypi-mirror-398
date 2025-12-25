import yaml, json, os, pathlib



def _loader(path:str, default = {}, _def=json.loads):
    _type = type(default)

    if not os.path.exists(path):
        return default

    try:
        with open(path,'r') as f:
            data = _def(f.read())
            if not isinstance(data,_type):
                return default
            return data
    except Exception:
        return default


def get_yaml(path:str, default = {}):
    return _loader(
        path,
        default = default, 
        _def = yaml.safe_load
    )
    
def get_json(path:str, default = {}):
    return _loader(
        path,
        default = default, 
        _def = json.loads
    )


def walker(_dir:str):
    for r,_,files in os.walk(_dir):
        for f in files:
            yield os.path.join(r,f)


def climber(_dir:str):
    _base = pathlib.Path(_dir)
    yield _dir
    for p in _base.parents:
        yield str(p)
    
