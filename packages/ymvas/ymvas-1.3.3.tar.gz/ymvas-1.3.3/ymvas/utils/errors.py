



class YException(Exception):

    def __init__(self, key:str , amsg = {}):
        from .messages import errors

        self._key  = key
        self._data = errors[key]
        self._msg  = self._data['msg']
        self._code = self._data['code']

        self._msg  = self._msg.format(**amsg)

        if 'color' in self._data:
            self._msg = self.color(self._data['color'], self._msg)

        super().__init__(self._msg)
    

    def color(self, color:str, msg:str) -> str:
        cls = {
            "red"    : lambda x: f"\033[31m{x}\033[0m",
            "green"  : lambda x: f"\033[32m{x}\033[0m",
            "yellow" : lambda x: f"\033[33m{x}\033[0m",
            "blue"   : lambda x: f"\033[34m{x}\033[0m",
        }

        return cls.get(
            color, 
            lambda x:x
        )(msg)
