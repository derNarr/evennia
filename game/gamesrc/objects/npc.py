
import random

from django.conf import settings
from ev import Script
from game.gamesrc.objects.character import Character

BASE_CHARACTER_TYPECLASS = settings.BASE_CHARACTER_TYPECLASS

class Npc(Character):
    """
    A NPC typeclass which extends the player class.

    """

    def at_object_creation(self):
        "Called at object creation."
        super(Npc, self).at_object_creation()
        self.db.is_aggressive = True
        self.db.in_combat = False
        self.db.belongs_to = set(["CAVE_FOLKS",])
        self.ndb.last_enemy = None


    def at_char_entered(self, character):
        """
        A simple is_aggressive check.
        Can be expanded upon later.

        """
        if self.db.in_combat:
            return
        if set.intersection(set(self.db.status), set(("UNCONSCIOUS", "DYING",
                                                      "DEAD"))):
            return
        if self.db.in_combat:
            return
        if set.intersection(set(self.db.status), set(("UNCONSCIOUS", "DYING",
                                                      "DEAD"))):
            return

        if self.db.is_aggressive:
            self.execute_cmd("say Graaah, die %s!" % character)
            self.execute_cmd("attack %s" % character)
            self.db.in_combat = True
            self.scripts.add(AttackTimer)
            return
        self.execute_cmd("say Greetings, %s!"% character)


    def attack(self):
        """
        Attacks character that has entered.

        """
        #players = [obj for obj in self.location.contents
        #           if utils.inherits_from(obj, BASE_CHARACTER_TYPECLASS) and not obj.is_superuser]
        if not self.ndb.combat_handler:
            self.db.in_combat = False
            return
        if set.intersection(set(self.db.status), set(("UNCONSCIOUS", "DYING",
                                                      "DEAD"))):
            return
        players = self.ndb.combat_handler.db.characters.values()
        # do not attack UNCONSCIOUS or DYING or DEAD characters
        # do not attack any character that belongs to one of your groups
        enemies = [pc for pc in players if ("CONSCIOUS" in pc.db.status and not
                                            set.intersection(set(self.db.belongs_to),
                                                             set(pc.db.belongs_to)))]
        if not enemies:
            self.db.in_combat = False
            self.execute_cmd("retreat")
            return
        if not self.ndb.last_enemy or not self.ndb.last_enemy in enemies:
            random.shuffle(enemies)
            self.ndb.last_enemy = enemies[0]
        self.execute_cmd("move %.2f,%.2f" % self.ndb.last_enemy.db.pos)
        self.execute_cmd("hit %s" % enemies[0])
        self.execute_cmd("commit")



class DevilRat(Npc):

    def at_object_creation(self):
        "Called at object creation."
        super(DevilRat, self).at_object_creation()
        self.ndb.sr.attributes.body = 2
        self.ndb.sr.attributes.agility = 5
        self.ndb.sr.attributes.reaction = 5
        self.ndb.sr.attributes.strength = 1
        self.ndb.sr.attributes.willpower = 3
        self.ndb.sr.attributes.logic = 2
        self.ndb.sr.attributes.intuition = 5
        self.ndb.sr.attributes.charisma = 5
        self.ndb.sr.attributes.edge = 2
        self.ndb.sr.attributes.essence = 6
        self.ndb.sr.attributes.magic = 4

        self.ndb.sr.skills.unarmed_combat = 5
        self.ndb.sr.skills.running = 2

        self.db.armor = 0

    @property
    def hit_damage(self):
        return self.ndb.sr.attributes.strength + 1

    @property
    def hit_damage_type(self):
        return "physical"






class AttackTimer(Script):
    """
    This script is what makes an enemy "tick".

    """

    def at_script_creation(self):
        "This sets up the script"
        self.key = "AttackTimer"
        self.desc = "Drives an Enemy's combat."
        self.interval = 1 # how fast the Enemy acts
        self.start_delay = True # wait self.interval before first call
        self.persistent = True


    def at_repeat(self):
        "Called every self.interval seconds."
        if self.obj.db.in_combat:
            self.obj.attack()
        else:
            self.stop()

