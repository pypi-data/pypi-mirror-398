import sys, os

from ymvas.utils import YException
from .operator import Operator


def _run():
    cli = Operator( src = os.getcwd() )

    if cli.version is True: # print version
        from .__init__ import __version__
        print( __version__ )
        sys.exit(0)
    

    # extract src
    if cli.debug:
        os.environ['ymvas-debug'] = 'true'

    # non repo commands
    if cli.init is not None:
        cli.use_init()
        return
    
    if cli.config is not None:
        cli.use_config()
        return

    if cli.compile is not None:
        cli.use_compile()
        return
    
    if cli.command is not None:
         cli.use_command()
         return

    cli.print_help()
    sys.exit(1)

def run():
    try:
        _run()
    except YException as e:
        print(e)
        sys.exit(1)

if __name__ == '__main__':
    try:
        run()
    except YException as e:
        print(e)
        sys.exit(1)
