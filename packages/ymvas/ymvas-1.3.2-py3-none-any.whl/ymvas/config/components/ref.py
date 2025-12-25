from __future__ import annotations

from functools import lru_cache
import json, re
from os.path import basename
from typing import Callable

import yaml

from ymvas.utils.errors import YException


class Ref:
    FALLBAKCS = {
        "yml" : "yaml",
    }

    STRUCTUED = [
        "yaml", 
        "json"
    ]

    VALID_TAGS = [
        "ref",
        "counter",
        "bill",
        "slot"
    ]

    EXPOSED = [
        "css"
    ]

    def __init__(self, src: str , config:dict = {}) -> None:
        self.src = src
        self._data = config

        self._content = ""
    
    @property
    def data(self) -> dict:
        return self._data
    
    @property
    @lru_cache
    def name(self) -> str:
        if self.filetype is None:
            return basename(self.src)
        return basename(self.src).rstrip(self.filetype).rstrip('.')

    @property
    @lru_cache
    def interpreted_language(self) -> str | None:
        data = self._data
        lang = data.get("lang",None)
        lang = Ref.FALLBAKCS.get(str(lang),lang)
        
        if lang in Ref.STRUCTUED:
            return lang

        lang = basename(self.src).split(".")[-1].lower()
        lang = Ref.FALLBAKCS.get(lang,lang)

        if lang in Ref.STRUCTUED:
            return lang

        return None
    
    @property
    @lru_cache
    def is_structured(self) -> bool:
        return self.interpreted_language in Ref.STRUCTUED
    
    @property
    @lru_cache
    def filetype(self) -> str | None:
        format = basename(self.src).split('.')[-1]
        if format == basename(self.src):
            return None
        return format


    @property
    @lru_cache
    def is_bytes_content(self) -> bool:
        
        try:
            with open(self.src,'rb') as f:
                while chunk := f.read(4096):
                    data = chunk.decode('utf-8')

                    # save it here so if it's read 
                    # corretly don't do it twice
                    self._content += data
            return False
        except UnicodeDecodeError:
            self._content = ""
            return True
        
    @property
    @lru_cache
    def tags(self) -> list[Tag]:
        
        if self.is_bytes_content:
            return []
        
        
        starters  = [(i,c) for i,c in enumerate(self._content) if c in ['<','>']]
        nstarters = len(starters)
        entries   = []

        for i, s in enumerate(starters):
            _next = starters[-1] if (i+1) == nstarters else starters[i+1]
            typ = s[1]

            if typ != '<':
                continue
            
            # found a tag
            name  = self._content[s[0]+1:_next[0]].split(' ')[0]
            name  = name.replace('\n','').replace('\t','')
            sname = name.replace("/",'')
            
            # skip tags that we don't need
            if not sname in Ref.VALID_TAGS:
                continue

            cnt = 0
            ends = None
            for j in range(i,nstarters):
                if starters[j][1] == "<":              cnt += 1
                if starters[j][1] == ">" and cnt != 0: cnt -= 1

                if starters[j][1] == ">" and cnt == 0:
                    ends = starters[j][0]
                    break

            if ends is None: continue

            entries.append({
                "name" : sname,
                "has_slash" : sname != name,
                "start" : s[0],
                "ends" : ends+1,
                "ender" : False if len(name) == 0 else (name[0] == "/"),
                "stupid" : len(name) == 0,
                "simple" : False if len(name) == 0 else (name[-1] == "/"),
                "single" : self._content[s[0]:ends+1].endswith("/>")
            })

        tags = []
        for i,e in enumerate(entries):
            name,start = e['name'], e['start']
            start_ends = e['ends']

            if e['stupid'] or e['simple'] or e['single']:
                tags.append({
                    "name"       : name ,
                    "tabs"       : self._content[0:start].split('\n')[-1],
                    "start"      : start,
                    "start_ends" : start_ends,
                    "close"      : None ,
                    "close_ends" : None ,
                })
                continue

            if e['ender']:
                continue

            cnt,ends = 0,None
            for j in range(i,len(entries)):
                if entries[j]['name'] != name or entries[j]['single']:
                    continue
                if not entries[j]['ender']:
                    cnt += 1
                if entries[j]['ender'] and cnt != 0:
                    cnt -= 1
                if entries[j]['ender'] and cnt == 0:
                    ends = entries[j]
                    break

            tags.append({
                "name"       : name         ,
                "tabs"       : self._content[0:start].split('\n')[-1],
                "start"      : start        ,
                "start_ends" : start_ends   ,
                "close"      : None if ends is None else ends['start'] ,
                "close_ends" : None if ends is None else ends['ends']  ,
            })
        
        _tags = []
        for t in tags:
            _tags.append(Tag(
                self,
                t['name'],
                t['start'],
                t['start_ends'],
                t['close'],
                t['close_ends'],
                t['tabs']
            ))

        return _tags
    
    def to_string(self , render:Callable, depth: str|None = None , into:str|None = None ) -> str:
        content , reach = "", 0
        
        for t in self.tags:
            s,e = t.begin, t.finish
            t = render(t)

            if s < reach:
                continue

            content += self._content[reach:s]
            content += t.render()
            reach = e

        content += self._content[reach:len(self._content)]

        # get step in content
        if not self.is_structured:
            return content
        
        sfunc = {
            "yaml" : yaml.safe_load,
            "json" : json.load
        }

        data = sfunc[str(self.interpreted_language)](content)
        if not depth is None:
            depthx = depth.strip("/")
            is_outer = depth.endswith('/')

            for level in depthx.split('/'):
                if level.isdigit():
                    if isinstance(data,list):
                        data = data[int(level)]
                        continue
                    else:
                        data = None
                        break

                elif isinstance(data,dict):
                    if level in data:
                        data = data[level]
                        continue
                    else:
                        data = None
                        break

                data = None
                break
        
            if is_outer:
                data = {depthx[-1]:data}
            elif data is None:
                return ""

        sfunc = {
            "yaml" : lambda x : yaml.dump(x, allow_unicode=True),
            "json" : lambda x : json.dumps(x, indent=2),
        }
        
        def _css(_data,l=0) -> str:
            nonlocal sfunc

            use_wpraps = [
                'px', '#', 'rgb', '-','.','rgb','var'
            ]
            if not isinstance(_data,dict):
                return sfunc[str(self.interpreted_language)](_data)

            ls = []
            for k,v in _data.items():
                if isinstance(v,dict):
                    v = _css(v,l=l+1)
                    ts = ('\t'*l)
                    ls.append( k + ("{\n" + ts ) + v + ts + "}")
                    continue
                _use = True
                for u in use_wpraps:
                    if u in v:
                        _use = False
                        break
                v = v.strip("\"'")
                if _use: v = f'"{v}"'
                ls.append(f"{k}:{v};")

            return ('\n' + ('\t' * l )).join(ls)

        sfunc['css'] = _css

        if not into is None:
            return sfunc[str(into)](data)
        
        return sfunc[str(self.interpreted_language)](data)

        
        
    @property
    def content(self) -> str:
        data = self.data.get('content',None)
        if not isinstance(data,str):
            raise YException('reference-not-cmpiled',amsg={
                "src" : self.src
            })
        return data

        
        
        






class Tag:

    def __init__(
        self,
        ref : Ref,
        name: str,
        start:int,
        start_ends:int,
        close:int | None = None,
        close_ends : int | None = None,
        tabs : str  = ""
    ) -> None:
        self.name = name
        self.ref = ref
        self._start = start
        self._start_ends = start_ends
        self._close = close
        self._close_ends = close_ends
        self._tabs = re.sub(r"[^\s]", " " , tabs )

        self._replacement = ""
    
    @property
    @lru_cache
    def start(self) -> str:
        return self.ref._content[self._start:self._start_ends]
    
    @property
    @lru_cache
    def raw(self) -> str:
        if self._close_ends is None:
            return self.start
        return self.ref._content[self._start:self._close_ends]

    @property
    @lru_cache
    def contents(self) -> str | None:
        if self._close_ends is None:
            return None
        return self.ref._content[self._start_ends:self._close]
    
    @property
    def begin(self) -> int:
        return self._start

    @property
    def finish(self) -> int:
        if self._close_ends is None:
            return self._start_ends
        return self._close_ends

    @property
    @lru_cache
    def slots(self) -> list[Tag]:
        _slots = []

        if self.contents is None:
            return []

        for t in self.ref.tags:
            if t._close_ends is None or self._close_ends is None:
                continue

            if t.name != 'slot':
                continue
            
            if t._start > self._start and t._close_ends < self._close_ends:
                continue

            _slots.append(t)

        return _slots
    
    def set_replace(self,content:str) -> None:
        self._replacement = content
    
    def sync_slots_from_ref(self, ref: Ref) -> None:

        if len(self.slots) == 0 and self.contents is not None:
            for t in ref.tags:
                if t.name != 'slot': continue
                if t.attrs.get('name',"main") != "main": continue
                t.set_replace(self.contents)
            return

        rslots = {}
        for t in ref.tags:
            if t.name != 'slot': continue
            name = t.attrs.get("name","main")
            rslots[name] = rslots.get(name,[])
            rslots[name].append(t)

        for s in self.slots:
            name = s.attrs.get('name','main')
            if name not in rslots:
                continue
            for r in rslots[name]:
                r.set_replace(s.contents)

        pass

    def render(self) -> str:
        if self._replacement == "":
            return ""
        
        # logic for tags if it's a counter
        if self.name == "counter":
            series = self.attrs.get('series')

            if not self._replacement.isnumeric():
                return "NaN"

            if series is None:
                return self._replacement
            
            if str(series).isnumeric():
                s = int(series)
                n = int(self._replacement)

                return str(int(n % s))
            
            return "NaN"

        replacement = self._replacement

        if not 'ignore-spaces' in self.attrs:
            replacement = f"\n{self._tabs}".join(replacement.split("\n"))
        
        return replacement
    
    @property
    @lru_cache
    def link(self) -> tuple[str|None,str|None,str|None,str|None]:
        attrs = self.attrs

        def _valid(x):
            if x == "":
                return None
            if isinstance(x,str):
                return x.strip()
            return None

        space  = _valid(attrs.get('space'))
        filep  = _valid(attrs.get('link'))
        depth  = _valid(attrs.get('part'))
        expect = _valid(attrs.get('expose'))

        if expect is None and self.ref.is_structured:
            expect = self.ref.interpreted_language
        
        exposable = Ref.STRUCTUED + Ref.EXPOSED
        if not expect in exposable:
            expect = None

        return space, filep, depth, expect

    @property
    @lru_cache
    def attrs(self) -> dict[str,str]:
        content = self.start

        ref = content.replace("/>","").replace('\n',' ').replace('>','')
        
        ref = " ".join([
            r for r in ref.split(' ') \
            if r.strip() != '' and '<' not in r and '>' not in r
        ])

        ref = ref.replace(" =","=").replace("= ","=")
        rei = [i for i, v in enumerate(ref) if v in ["'",'"']]

        dc = {"'":0,'"':0}
        lt = {"'":None,'"':None}
        pairs = []
        for c in rei:
            r = ref[c]
            n = dc[r]

            if n != 0: # close
                ref[c]
                dc[r] = 0
                o = "'" if r != "'" else '"'
                dc[o] = 0
                s,e = (lt[r],c)
                cnn = ref[s:e+1]
                pairs.append((s,e,cnn))
                lt[r] = None
            else:
                dc[r] += 1
                lt[r] = c

        dc = {str(i):v[2] for i,v in enumerate(pairs)}
        for k,v in dc.items():
            ref = ref.replace(v,f'{k}'.strip("'\"\n"))

        ref  = ref.split(" ")
        data = {}
        for a in ref:
            g = a.split('=')
            data[g[0]] = True if len(g) < 2 else dc.get(g[1],None)
            i = data[g[0]]
            if isinstance(i,str):
                data[g[0]] = i[1:-1]

        return data

