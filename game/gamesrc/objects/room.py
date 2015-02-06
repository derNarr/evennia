"""

Template module for Rooms

Copy this module up one level and name it as you like, then
use it as a template to create your own Objects.

To make the default commands (such as @dig) default to creating rooms
of your new type, change settings.BASE_ROOM_TYPECLASS to point to
your new class, e.g.

settings.BASE_ROOM_TYPECLASS = "game.gamesrc.objects.myroom.MyRoom"

Note that objects already created in the database will not notice
this change, you have to convert them manually e.g. with the
@typeclass command.

"""

from ev import Room as DefaultRoom
from ev import utils

from game.gamesrc.objects.character import Character
from game.gamesrc.objects.npc import Npc


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    pass

    def at_object_receive(self, obj, source_location):
        if utils.inherits_from(obj, Npc): #an NPC has entered
            pass
        else:
            if utils.inherits_from(obj, Character):
                #A PC has entered, NPC is caught above
                # cause the character to look around
                obj.execute_cmd('look')
                for item in self.contents:
                    if utils.inherits_from(item, Npc):
                        #An NPC is in the room
                        item.at_char_entered(obj)

