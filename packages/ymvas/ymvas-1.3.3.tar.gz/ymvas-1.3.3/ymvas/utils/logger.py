import logging, os
from .system import get_global_config

_logger = logging.getLogger('ymvas')
cnf = get_global_config()

    
class logger:

    def __init__(self, section:str = ""):
        self.__section = section

        # get enviroment variables firts
        # then get configuration
        # if debug is enabled print the info

        debug = str(os.environ.get(
            "ymvas-debug",cnf.get("ymvas-debug",False)
        )).lower() == 'true'

        debug_sections = str(os.environ.get(
            'ymvas-debug-sections',cnf.get(
            'ymvas-debug-sections','all'
        ))).split(',')

        self.debug = (
            debug and (
                section in debug_sections or
                "all" in debug_sections
            )   
        )

    @property
    def section(self):
        if self.__section != "":
            return f"{self.__section} : "
        return ""

    def danger(self,msg:str):
        if self.debug:
            print(f"{self.section}\033[21m{msg}\033[0m")
            return
            
        _logger.danger(f"{self.section}\033[21m{msg}\033[0m")


    def info(self,msg:str):
        if self.debug:
            print(f"{self.section}{msg}")
            return
        
        _logger.info(f"{self.section}{msg}")
    
    def warning(self,msg:str):
        if self.debug:
            print(f"{self.section}{msg}")
            return
        _logger.info(f"{self.section}{msg}")
