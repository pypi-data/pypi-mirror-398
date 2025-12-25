from os.path import dirname, join, exists, relpath
import os, shutil

from ymvas.config.components.event import Event
from ymvas.config.components.contact import Contact
from ymvas.utils import system, walker
from .referer import Referer

# for types
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ymvas.settings import Settings



class Compiler( Referer ):
    
    def __init__( self, settings:"Settings", destination:str ):
        self.settings    = settings
        self.destination = destination
        self.is_main     = settings.is_main

        self.cache = {}

    def clean(self):
        if not exists(self.destination):
            return True
        shutil.rmtree(self.destination)
        return True
    

    def run( self ):
        self.clean()

        config = {}
        os.makedirs( self.destination , exist_ok = True )
        
        # end preparation 
        self._compile_settings(  config )
        self._compile_schedules( config )
        self._compile_endpoints( config )

        return config

    def _compile_settings( self, config ):
        if not self.is_main:
            return

        settings  = self.settings
        ysettings = settings.get_repo_config()

        if ysettings.has_avatar:
            shutil.copy2(
                str( ysettings.avatar_fullpath ),
                join(self.destination , str(ysettings.avatar_basename) )
            )

            config["avatar"] = {
                "src"    : ysettings.avatar_basename,
                "origin" : ysettings.avatar_relpath
            }

    def _compile_schedules( self , config ):
        stg = self.settings
        yse = stg.get_repo_events_config()
        
        if not yse.calendar_create:
            return
        
        events = []
        # function to add all events in the main list for 
        # main repo and submodules
        def _add_events( stgs: "Settings" ):
            nonlocal events, yse
            for file in walker( stgs.d_events ):
                e = Event( file )
                if not e.active:
                    continue

                events.append(e)
        
            # fetch birthday events if this are allowed
            if  yse.calendar_adds_birthdays:
                for file in walker( stg.d_contacts ):
                    c = Contact( file )
                    e = c.get_birthday_event()

                    if e is None or not e.active:
                        continue

                    events.append(e)
        
        # add events for main repo
        _add_events( stg )

        # add events from submodules
        submodules = yse.calendar_submodules
        for module in submodules:
            # TODO store events for submodules in bare repo (if posible)
            # and if this ones have no updates just pull latest events
            # to not process them again
            _add_events( module )

        if len(events) == 0:
            return
       
        events = [ e.ics_content for e in events if e.ics_content ]
        domain = system.ymvas_domain()

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            f"PRODID:{domain}",
            "\n".join(events),
            "END:VCALENDAR"
        ]

        with open(join(self.destination,'calendar.ics'),'w') as f:
            config['calendar'] = 'calendar.ics'
            f.write("\n".join(ics_lines))


    def _compile_endpoints( self , config ):
        settings  = self.settings
        esettings = settings.get_repo_endpoints_config()

        config['files'] = {}

        for e in esettings.endpoints:
            data = e.compile( self._render )

            if data is None:
                continue
            
            origin = settings.relpath(e.src)
            orirel = relpath(e.src,settings.d_endpoints)
            destin = orirel

            if e.is_valid_converts:
                destin = orirel.rstrip(e.filetype)
                destin = destin + str(e.filetype_converts)

            relp = join(self.destination, destin)
            dirn = dirname(relp)
            os.makedirs(dirn , exist_ok = True )

            with open(relp,"wb") as f:
                f.write(data)
            
            config['files'][orirel] = {
                "origin"      : origin,
                "destination" : destin,
                "conf"        : e.config
            }
            
        
