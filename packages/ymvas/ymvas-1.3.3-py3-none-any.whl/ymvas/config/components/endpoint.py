from __future__ import annotations

from functools import lru_cache
from typing import Callable
from .ref import Ref


class Endpoint(Ref):
    
    CONVERTS_AVALIABLE = {
        "html" : ["pdf"],
        "svg"  : ["svg"],
        "md"   : ["html"]
    }

    def __init__(self, src:str, config: dict= {}) -> None:
        super().__init__(src,config)

    @property
    def config(self) -> dict:
        data = {}

        if self.is_valid_converts:
            data['format'] = self.filetype_compile
            data['into'] = self.filetype_converts

        return data
    
    @property
    def is_valid_converts(self) -> bool:
        if self.filetype_compile is None \
         or self.filetype_converts is None:
            return False

        avaliable = Endpoint.CONVERTS_AVALIABLE[self.filetype_compile]

        return self.filetype_converts in avaliable

    @property
    @lru_cache
    def filetype_compile(self) -> str | None:
        data = self.data
        format = self.filetype

        if 'format' in data:
            format = data.get('format')

        if not isinstance(format,str):
            return None

        if format in Endpoint.CONVERTS_AVALIABLE:
            return format

        return None
    
    @property
    @lru_cache
    def filetype_converts(self) -> str | None:
        data = self.data
        if not 'into' in data:
            return None
        if not isinstance(data['into'],str):
            return None
        return data['into']
        
    def compile(self, render:Callable ) -> bytes | None:

        # basically non ref files
        if self.is_bytes_content:
            with open(self.src,'rb') as f:
                return f.read()

        content = self.to_string( render )
        content = content.encode("utf-8")

        if not self.is_valid_converts:
            return content

        
        converters = {
            "html" : {
                "pdf" : self.__html_to_pdf
            },
            "svg" : {
                "png" : self.__svg_to_png
            },
            "md" : {
                "html" : self.__md_to_html
            }
        }
        
        vtypes = converters[str(self.filetype_compile)]
        _defmk = vtypes[self.filetype_converts]

        return _defmk(
            content,
            self.data
        )

    
    






    # private modifiers
    def __html_to_pdf(self, content: bytes , conf:dict = {}) -> bytes | None:
        options = {
            'margin-top'    : str(conf.get( 'margin-top'    , '0.0in' )),
            'margin-right'  : str(conf.get( 'margin-right'  , '0.0in' )),
            'margin-bottom' : str(conf.get( 'margin-bottom' , '0.0in' )),
            'margin-left'   : str(conf.get( 'margin-left'   , '0.0in' )),
        }
        try:
            import pdfkit
            data = pdfkit.from_string(
                content.decode('utf-8'),
                False,
                options = options
            )

            if isinstance(data,bytes):
                return data

            print(f"[pdfkit] failed to create file for [{self.src}]")

        except OSError:
            print(
                "[pdfkit] failed to create file, "
                "please install all the depedencies required!"
            )

        return content


    def __svg_to_png(self,content:bytes,conf:dict = {}) -> bytes | None:
        try:
            from cairosvg import svg2png
            return svg2png(bytestring=content)
        except Exception:
            print(
                '[cairosvg] failed to create file, '
                'please install all the depedencies required!'
            )
        return content


    def __md_to_html(self,content:bytes,conf:dict = {}) -> bytes:
        try:
            import markdown
            return markdown.markdown(
                content.decode('utf-8')
            ).encode('utf-8')
        except Exception:
            print(
                '[markdown] failed to create file, '
                'please install all the depedencies required!'
            )
        return content





