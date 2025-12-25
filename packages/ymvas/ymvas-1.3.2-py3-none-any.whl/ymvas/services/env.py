from __future__ import annotations


import inspect, os, json, yaml, io
from os.path import exists, dirname, isdir, join, basename

from dotenv.main import DotEnv

from ymvas.utils import YException, climber
from ymvas.config.components.ref import Ref



class Environ(Ref):

    POSIBLES = [
        '.env'      ,
        ".env.json" ,
        ".env.yaml" ,
        ".env.yml"  ,
    ]

    def __init__( self, src: str = '.env' ):
        caller = inspect.stack()[1]
        source = dirname( caller.filename )
        
        self.src = join(source, src)
        if src != ".env":
            pass
            
        elif not exists(self.src) or isdir(self.src):
            for d in climber(self.src):
                for t in Environ.POSIBLES:
                    f = join(d,t)
                    if not exists(f):
                        continue
                    self.src = f
            
                if exists(join(d,'.git')):
                    break

        self.is_env = basename(self.src) == '.env'
        Ref.__init__(self,self.src)
        self._vars = {}

    def __parse(self) -> dict:
        if self.is_bytes_content:
            return {}

        if len(self.tags) != 0:
            # todo get settings
            # and parse references
            pass

        if self.is_env:
            e = DotEnv( None, stream = io.StringIO(self._content))
            return e.dict()
        
        lang = self.interpreted_language

        if lang == 'json':
            return json.loads(self._content)
        if lang == 'yaml':
            return yaml.safe_load(self._content)
        
        return {}


    def load(self):
        self._vars = self.__parse()
        
        if not isinstance(self._vars,dict):
            return {}

        for k, v in self._vars.items():
            if isinstance(v,(dict,list)):
                os.environ[k] = json.dumps(v)
            else:
                os.environ[k] = str(v)

        return self._vars

    def __get__(self,key):
        return os.environ.get(key)

    def get(self,key,default=None):
        return os.environ.get(key,default)

    def set(self,key:str,value:str):
        os.environ[key] = value
        self.data[key] = value

    def save(self):
        if len(self.tags) != 0:
            raise YException('complex-secret', {
                'src' : self.src
            })

        lang = self.interpreted_language

        if lang == 'json':
            open(self.src,'w').write(json.dumps(self._vars,indent=2))
            return
        
        if lang == 'yaml':
            open(self.src,'w').write(yaml.dump(self._vars))
            return
