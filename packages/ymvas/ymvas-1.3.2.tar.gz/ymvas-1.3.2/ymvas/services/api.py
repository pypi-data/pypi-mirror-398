import requests

class API:
    url = 'http://api.ymvas.com'

    def __init__(
        self,
        auth:str ,
        is_ssh:bool = False
    ):

        self.auth = auth
        pass


    def post(self, fragment, *args,**kwargs):
        return requests.post( self.url + fragment , *args, **kwargs )

    def tmp_add_key(self, name, content ):
        self.post( '/tmp_add_key' ,
            data = {
                "name" : name,
                "content" : content ,
                "pasw" : self.auth,
            }
        )
