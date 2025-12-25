
from os.path import join, exists
from ymvas.config.components.ref import Ref, Tag
from ymvas.utils.files import walker


# for types
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ymvas.settings import Settings



class Referer:

    def __init__(self, settings : "Settings" ) -> None:
        self.settings = settings
        self.cache    = {}
    

    def filter( self, fragment:str ) -> list[Ref]:
        stg = self.settings 
        
        refs = []

        for f in walker(stg.d_references):
            data = f.replace(stg.d_references,'')
            if not fragment in data:
                continue
            
            r = Ref(f)

            compiled_content = r.to_string( self._render )
            r._data['content'] = compiled_content

            refs.append( r )

        return refs
    
    def _render(self, tag:Tag ):
        repo, file, depth, into = tag.link
            
        if file is None:
            # no link provided
            return tag
            
        if repo is None:
            repo = self.settings.alias

        module = self.settings.modules.get(str(repo))
        if module is None:
            return tag
        
        rsrc = join(module.d_references,file)
        if not exists(rsrc):
           return tag

        ref = None
        if tag.ref.src == rsrc:
            # if self reference
            ref = tag.ref
        else:
            ref = self.cache.get(rsrc, Ref(rsrc))
                
        tag.sync_slots_from_ref( ref )
        tag.set_replace( ref.to_string( self._render, depth, into) )
        
        # store refs for next iteration
        if not tag.ref.src in self.cache:
            self.cache[tag.ref.src] = tag.ref
        if not rsrc in self.cache:
            self.cache[rsrc] = ref
            
        return tag

