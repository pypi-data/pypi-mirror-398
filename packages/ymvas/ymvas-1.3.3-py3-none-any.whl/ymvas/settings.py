from __future__ import annotations

from os.path import (
    exists,
    join,
    relpath,
    isdir
)
import configparser
from functools import lru_cache
from pathlib import Path

from ymvas.config.ycommands import YCommandsSettings
from ymvas.config.yendpoints import YEndpointsSettings
from ymvas.config.yevents import YEventsSettings
from ymvas.config.ysettings import YSettings

from .utils import (
    system, 
    find_root,
)


class Settings:
    # if path provided leads to a repo upstream
    is_repo      : bool = False
    is_module    : bool = False
    is_ymvas     : bool = False # if repos if fetched from ymvas

    # paths
    root         : str # /root             -> folder of the repo
    git          : str # /root/.git        -> folder , if module -> /root/../../.git
    hooks        : str # /root/.git/hooks  -> folder , if module -> /root/../../.git/hooks
    ymvas        : str # /root/.ymvas      -> folder

    # repo info
    url          : str # example  -> git@ymvas.com/vas/ymvas.git
    name         : str # from url -> ymvas
    user         : str # from url -> vas

    # ymvas important folders
    d_references : str
    d_commands   : str
    d_settings   : str
    d_tasks      : str
    d_events     : str
    d_secrets    : str
    d_finance    : str
    d_hooks      : str
    d_endpoints  : str
    d_documents  : str
    d_contacts   : str
    d_spaces     : str


    # ymvas config files
    f_settings            : str
    f_settings_endpoints  : str
    f_settings_references : str
    f_settings_secrets    : str
    f_settings_tasks      : str
    f_settings_finance    : str
    f_settings_hooks      : str

    def __init__( self , pwd:str ):
        self.active = True
        self.root, self.is_repo = find_root( pwd )

        if self.is_repo:
            self._setup_repo_paths()

      
    # git command helpers
    @property
    def _git(self):
        return f"git --git-dir='{self.git}' --work-tree='{self.root}' "

    def _setup_repo_paths( self ):
        _git      = join( self.root , '.git' )
        is_module = not isdir( _git )

        if not exists(_git):
            return

        if is_module:
            with open( _git , 'r' ) as f:
                _git = Path( f.read().split("gitdir:")[1].strip() )
                _git = str( Path(self.root) / _git )
        

        self.git       = _git
        self.hooks     = join( _git , 'hooks' )
        self.is_module = is_module

        ######### config #########
        cnf = configparser.ConfigParser()
        cnf.read(join( _git , 'config' ))

        _url = None
        for section in cnf.sections():
            if 'origin' in section and 'remote':
                _url = cnf[section].get('url',None)
                break

        user, name, is_ymvas = system.git_url_parse(_url)

        self.is_ymvas = is_ymvas
        self.user     = user
        self.name     = name
        self.url      = _url

        self.ymvas        = join( self.root , '.ymvas'     )
        self.d_references = join( self.ymvas, 'references' )
        self.d_commands   = join( self.ymvas, 'commands'   )
        self.d_settings   = join( self.ymvas, 'settings'   )
        self.d_tasks      = join( self.ymvas, 'tasks'      )
        self.d_events     = join( self.ymvas, 'events'     )
        self.d_secrets    = join( self.ymvas, 'secrets'    )
        self.d_finance    = join( self.ymvas, 'finance'    )
        self.d_hooks      = join( self.ymvas, 'hooks'      )
        self.d_endpoints  = join( self.ymvas, 'endpoints'  )

        # /repo folders if account
        if self.is_main:
            self.d_endpoints = join(self.root, 'endpoints' )
            self.d_documents = join(self.root, 'documents' )
            self.d_contacts  = join(self.root, 'contacts'  )
            self.d_finance   = join(self.root, 'finance'   )
            self.d_spaces    = join(self.root, 'spaces'    )

        # sttings files
        self.f_settings            = join(self.d_settings, 'settings.yaml'   )
        self.f_settings_endpoints  = join(self.d_settings, 'endpoints.yaml'  )
        self.f_settings_commands   = join(self.d_settings, 'commands.yaml'   )
        self.f_settings_references = join(self.d_settings, 'references.yaml' )
        self.f_settings_secrets    = join(self.d_settings, 'secrets.yaml'    )
        self.f_settings_tasks      = join(self.d_settings, 'tasks.yaml'      )
        self.f_settings_finance    = join(self.d_settings, 'finance.yaml'    )
        self.f_settings_hooks      = join(self.d_settings, 'hooks.yaml'      )
        self.f_settings_events     = join(self.d_settings, 'events.yaml'     )
    
    @property
    def alias( self ) -> str:
        if self.user is None:
            return self.name
        return f"{self.user}/{self.name}"

    @property
    def is_main( self ) -> bool:
        if not hasattr(self,'user'):
            return False
        if self.user is None:
            return False
        return self.user == self.name

    @lru_cache( maxsize = None )
    def relpath( self, path:str ) -> str:
        return relpath( path , self.root )
    
    # REPOSITORY SETTINGS
    @lru_cache
    def get_repo_config(self) -> YSettings:
        return YSettings( self )

    @lru_cache
    def get_repo_events_config( self ) -> YEventsSettings:
        return YEventsSettings( self )
    
    @lru_cache
    def get_repo_endpoints_config( self ) -> YEndpointsSettings:
        return YEndpointsSettings( self )
    
    @lru_cache
    def get_repo_comands_config( self ) -> YCommandsSettings:
        return YCommandsSettings( self )
    
    # source repository
    @property
    @lru_cache
    def source(self) -> Settings | None:
        if self.is_main:
            return self
        
        for _,m in self.modules.items():
            if m.is_main:
                return m

    @property
    @lru_cache
    def modules(self) -> dict[str,Settings]:
        file = join( self.root , '.gitmodules' )

        if self.is_module:
            modules = join(".git","modules")
            fragment = modules + self.git.split(modules)[-1]
            main_path = self.git.replace(fragment,"")
            main_settings = Settings(main_path)
            return main_settings.modules
        
        modules = { self.alias: self }

        if not exists( file ):
            return modules

        with open(file) as f:
            cnf = configparser.ConfigParser()
            cnf.read_string( f.read() )
            
            for s in cnf.sections():
                p = cnf[s].get( 'path', None )
                u = cnf[s].get( 'url' , None )

                if not 'submodule' in s or p is None or u is None:
                    continue
                
                s = Settings( p )
                user, name, is_ymvas = system.git_url_parse(u)
                s.user = user
                s.name = name
                s.is_ymvas = is_ymvas

                modules[s.alias] = s
        
        return modules
