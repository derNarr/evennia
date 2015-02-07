"""

Template for Characters

Copy this module up one level and name it as you like, then
use it as a template to create your own Character class.

To make new logins default to creating characters
of your new type, change settings.BASE_CHARACTER_TYPECLASS to point to
your new class, e.g.

settings.BASE_CHARACTER_TYPECLASS = "game.gamesrc.objects.mychar.MyChar"

Note that objects already created in the database will not notice
this change, you have to convert them manually e.g. with the
@typeclass command.

"""

from __future__ import division

import math

import game.gamesrc.world.dice as dice
import game.gamesrc.world.sr5 as sr5
from game.gamesrc.world.rule import Boni
from ev import Character as DefaultCharacter


class Character(DefaultCharacter):
    """
    The Character is like any normal Object (see example/object.py for
    a list of properties and methods), except it actually implements
    some of its hook methods to do some work:

    at_basetype_setup - always assigns the default_cmdset to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead)
    at_after_move - launches the "look" command
    at_post_puppet(player) -  when Player disconnects from the Character, we
                    store the current location, so the "unconnected" character
                    object does not need to stay on grid but can be given a
                    None-location while offline.
    at_pre_puppet - just before Player re-connects, retrieves the character's
                    old location and puts it back on the grid with a "charname
                    has connected" message echoed to the room

    """

    def at_object_creation(self):
        """
        Called only at initial creation.

        """
        self.ndb.sr = sr5.Sr5Character(self.db)

        self.db.status = ["CONSCIOUS",]
        # status ["CONSCIOUS", "UNCONSCIOUS", "DYING", "DEAD"]
        self.db._damage_stun = 0
        self.db._damage_physical = 0
        self.db.known_spells = []
        self.db.sustained_spells = list()
        self.db.boni = Boni()

        self.db.armor = 12
        self.db.pos = (0, 0)

        # which group do you belong to (determines who might attack you)
        self.db.belongs_to = set()

        # wearing
        #self.db.wear


    def at_after_move(self, source_location):
        """
        Default is to look around after a move
        NOTE:  This has been moved to room.at_object_receive

        """
        #self.execute_cmd('look')
        pass


    def at_init(self):
        # Sr5Character is coded in a way that it recovers the data when the
        # data exists.
        super(Character, self).at_init()
        self.ndb.sr = sr5.Sr5Character(self.db)


    # properties

    @property
    def limit_mental(self):
        return int(math.ceil((self.ndb.sr.attributes.logic * 2 +
                              self.ndb.sr.attributes.intuition +
                              self.ndb.sr.attributes.willpower) / 3))

    @property
    def limit_physical(self):
        return int(math.ceil((self.ndb.sr.attributes.strength * 2 +
                              self.ndb.sr.attributes.body +
                              self.ndb.sr.attributes.reaction) / 3))

    @property
    def limit_social(self):
        return int(math.ceil((self.ndb.sr.attributes.charisma * 2 +
                              self.ndb.sr.attributes.willpower +
                              self.ndb.sr.attributes.essence) / 3))

    @property
    def limit_astral(self):
        return max(self.limit_mental, self.limit_social)

    @property
    def damage_physical_max(self):
        return int(8 + math.ceil(self.ndb.sr.attributes.body / 2))


    @property
    def damage_stun_max(self):
        return int(8 + math.ceil(self.ndb.sr.attributes.willpower / 2))


    @property
    def damage_stun(self):
        return self.db._damage_stun


    @damage_stun.setter
    def damage_stun(self, new_stun_damage):
        overflow = max(0, new_stun_damage - self.damage_stun_max)
        self.db._damage_stun = new_stun_damage - overflow

        if self.db._damage_stun == self.damage_stun_max:
            self.status_remove("CONSCIOUS")
            self.db.status.append("UNCONSCIOUS")
            self.cmdset.add("game.gamesrc.commands.cmdset.DeadCharacterCmdSet")

        if overflow:
            self.damage_physical += math.floor(overflow / 2)


    @property
    def damage_physical(self):
        return self.db._damage_physical


    @damage_physical.setter
    def damage_physical(self, new_physical_damage):
        self.db._damage_physical = new_physical_damage
        if self.db._damage_physical >= self.damage_physical_max:
            self.status_remove("CONSCIOUS")
            self.status_remove("UNCONSCIOUS")
            self.db.status.append("DYING")
            self.cmdset.add("game.gamesrc.commands.cmdset.DeadCharacterCmdSet")
        if self.db._damage_physical > (self.damage_physical_max +
                                       self.ndb.sr.attributes.body):
            self.status_remove("CONSCIOUS")
            self.status_remove("UNCONSCIOUS")
            self.status_remove("DYING")
            self.db.status.append("DEAD")
            self.cmdset.add("game.gamesrc.commands.cmdset.DeadCharacterCmdSet")


    @property
    def initiative_dice(self):
        return max(1, min(5, self.db._initiative_dice))


    @initiative_dice.setter
    def initiative_dice(self, value):
        old_dice = self.initiative_dice
        self.db._initiative_dice = value
        new_dice = self.initiative_dice
        diff_dice = new_dice - old_dice
        if diff_dice == 0:
            return
        elif diff_dice > 0:
            for ii in range(diff_dice):
                self.db._initiative_rolled_dice += dice.roll_die()
        elif diff_dice < 0:
            for ii in range(-diff_dice):
                self.db._initiative_rolled_dice -= dice.roll_die()


    @property
    def hit_damage(self):
        return self.ndb.sr.attributes.strength


    @property
    def hit_damage_type(self):
        return "stun"


    # utility

    def bonus(self, attribute):
        """
        Returns the summed boni and mali that apply to an attribute (or to
        "initiative", "defense", "spellcasting"...) as an integer.

        Boni available only in combat are added by CharacterCombatInformation
        instance.

        """
        # general mali
        bonus = - (self.damage_stun // 3)
        bonus += - (self.damage_physical // 3)
        # for initiative only damage modifiers apply
        if attribute == "initiative":
            return bonus + self.db.boni.get(attribute)
        number_of_sustained_spells = len(self.db.sustained_spells)
        bonus += - 2 * number_of_sustained_spells
        return bonus + self.db.boni.get(attribute)


    def resist(self, modified_damage_value, type_, armor_piercing=0):
        """
        Resist with body + modified_armor_value the modified_damage_value (int)
        of type_ ("stun", "physical") and apply damage to damage track.

        positive armor_piercing increases armor

        Returns dict with keys "dp_resist", "hits_resist", "glitch_resist",
        "damage", "damage_type".

        """
        response = dict()
        # TODO include elementary damage like fire or acid damage and the
        # specific resistance
        if self.db.armor > 0:
            modified_armor_value = max(0, self.db.armor + armor_piercing)
        else:
            modified_armor_value = 0
        dice_pool = self.ndb.sr.attributes.body + modified_armor_value
        if modified_damage_value < modified_armor_value:
            type_ = "stun"
        hits, glitch = dice.roll_dice_pool(dice_pool)
        damage = max(0, modified_damage_value - hits)
        if type_ == "stun":
            self.damage_stun += damage
        else:
            self.damage_physical += damage
        response["damage_value"] = modified_damage_value
        response["dp_resist"] = dice_pool
        response["hits_resist"] = hits
        response["glitch_resist"] = glitch
        response["damage"] = damage
        response["damage_type"] = type_
        return response


    def resist_fatigue(self, damage_value):
        """
        Resist with body + willpower.

        Returns dict with keys "dp_fatigue", "hits_fatigue", "glitch_fatigue",
        "damage", "damage_type".

        """
        response = dict()
        dice_pool = self.ndb.sr.attributes.body + self.ndb.sr.attributes.willpower
        damage_type = "stun"
        hits, glitch = dice.roll_dice_pool(dice_pool)
        damage = max(0, damage_value - hits)
        self.damage_stun += damage
        response["damage_value"] = damage_value
        response["dp_fatigue"] = dice_pool
        response["hits_fatigue"] = hits
        response["glitch_fatigue"] = glitch
        response["damage"] = damage
        response["damage_type"] = damage_type
        return response



    def status_remove(self, value):
        try:
            self.db.status.remove(value)
        except ValueError:
            pass

