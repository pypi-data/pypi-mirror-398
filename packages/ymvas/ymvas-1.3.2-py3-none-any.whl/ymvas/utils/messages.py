from . import (
    global_config_file,
    global_config_dir
)

errors = {
    # system errors
    "global-dir-not-created" : {
        "msg"  : (
            "Unable to create global directory, please check permisions for this directory "
            f"[{global_config_dir()}] !"
        ),
        "code" : "501"
    },
    "global-config-not-created" : {
        "msg" : (
            "Unable to create global config file please check permisions!"
            f"[{global_config_file()}]"
        ),
        "code" : "502"
    },
    "global-config-misconfigured": {
        "msg" : (
            f"Unable to parse config file [{global_config_file()}]"
            ", please remove it or fix the contents"
        ),
        "code" : "503"
    },









    
    'complex-secret' : {
        'msg' : (
            "[{src}] contains references and can't be updated!"
        ),
        'code' : "401"
    },
    'invalid-directory' : {
        'msg' : (
            "[{src}] is not a valid repositoy!"
        ),
        'code' : "402",
        "color" : "yellow"
    },
    'reference-not-cmpiled' : {
        'msg' : (
            "[{src}] was not complied correctly, please use Referer properly!"
        ),
        'code' : "403"
    },



    # operator errors
    'init-help' : {
        "msg": (
            "init was not setup correctly, valid arguments: {choices} \n" 
            "try this: \n"
            ">> ym init default \n"
            ">> ym init account "
        ), 
        "code" : "100",
        "color" : "yellow"
    },
    'config-help' : {
        "msg": (
            "config neds more arguments to be used: {choices}\n"
            "try with:\n"
            ">> ym config set --global-src=\"/path/for/your/global/repo\"]\n"
            ">> ym config get --global-src\n"
            ">> ym config show \n"
            "\n"
            "avaliable flags:\n{flags}\n"
        ), 
        "code" : "101",
        "color" : "yellow"
    }


}
