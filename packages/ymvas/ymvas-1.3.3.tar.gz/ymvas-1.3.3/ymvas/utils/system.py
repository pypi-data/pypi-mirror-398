from __future__ import annotations

import json, os, platform
from functools import lru_cache
from . import YException

_config = None

@lru_cache(maxsize=None)
def sys_platform() -> str:
    system  = platform.system()
    shell   = os.environ.get("SHELL", "")
    msystem = os.environ.get("MSYSTEM", "")
    
    # Detect Git Bash on Windows
    is_windows_git_bash = (system == "Windows") and (
        "bash" in shell or msystem.startswith("MINGW")
    )

    if is_windows_git_bash:
        return "git-bash"
    elif system == "Windows":
        return "widnows"
    elif system == "Darwin":
        return "mac"
    return 'unix'


@lru_cache(maxsize=None)
def global_config_dir() -> str:
    return os.path.join({
        "git-bash" : os.path.expanduser("~/.config"),
        "widnows"  : os.environ.get("APPDATA", os.path.expanduser(
            "~\\AppData\\Roaming"
        )),
        "mac"      : os.path.expanduser("~/Library/Application Support"),
        'unix'     : os.environ.get("XDG_CONFIG_HOME", os.path.expanduser(
            "~/.config"
        ))
    }.get(sys_platform(), '~/.config'), 'ymvas')


@lru_cache(maxsize=None)
def global_config_file() -> str:
    return os.path.join(global_config_dir(),'config.json')


def get_global_config() -> dict:
    global _config

    if _config is not None:
        return _config

    f = global_config_file()
    if not os.path.exists(f):
        _config = {}
        return _config
    try:
        with open(f) as fs:
            x = json.loads(fs.read())
            if not isinstance(x,dict):
                raise YException('global-config-misconfigured')
            _config = x
    except FileNotFoundError:
        _config = {}
    except json.JSONDecodeError:
        raise YException("global-config-misconfigured")
        
    return _config


@lru_cache
def ymvas_domain() -> str:
    cnf = get_global_config()
    data = cnf.get('ymvas-domain')
    
    if data is None:
        return "ymvas.com"

    return data


@property
@lru_cache
def server_ssh_address() -> str:
    cnf = get_global_config()
    return str(cnf.get(
        "ymvas-server-url",
        "ssh://git@" + str(ymvas_domain()) + "/{repo}.git"
    ))


def setup_global_config(**kwargs) -> None:
    "saves the global configuration"

    cnf = get_global_config()
    if 'version' in cnf:
        return

    _dir = global_config_dir()
    try:
        os.makedirs(_dir, exist_ok = True )

    except PermissionError:
        raise YException('global-dir-not-created')
    
    if not os.path.exists(_dir):
        raise YException('global-dir-not-created')

    _file = global_config_file()
    from ..__init__ import __version__
    
    try:

        with open(_file,'w') as f:
            kwargs['version'] = __version__
            f.write(json.dumps(kwargs,indent=2))

    except PermissionError:
        raise YException('global-config-not-created')
    

def update_global_config(**kwargs) -> None:
    global _config

    setup_global_config()
    _file = global_config_file()
    
    cnf = get_global_config()
    
    for k,v in kwargs.items():
        cnf[str(k)] = str(v)

    try:
        with open(_file,'w') as f:
            f.write(json.dumps(cnf))
    except PermissionError:
        raise YException('global-config-not-created')


@lru_cache
def git_url_parse( url:str ) -> tuple[str|None,str,bool]:
    is_ymvas = f"@{ymvas_domain()}" in url
    name = os.path.basename(url).replace('.git','')

    # get repo user 
    user1 = url.split('@')[-1]
    user  = user1.replace(os.path.basename(url),'')
    user  = os.path.basename(user.strip('/'))
    user  = user.split(':')[-1]
    user  = user.strip('/')
    user  = user if '/' not in user else None

    if user is not None:
        user = None if user1.startswith( user ) else user

    return user, name, is_ymvas

