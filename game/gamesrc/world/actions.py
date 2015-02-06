#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
In this module the rules for doing something within the game mechanics are
implemented.

Everything that can be done is put into an Action. Normally, this Action will
be set up for a specific situation by creating an instance of the action. Then
it can be applied (instance.apply()).

Do
==
* Grab and modify all variables and information that you need. Especially those
  within the character or the information classes.
* Return a dict with all outcomes of the action that can be used to message
  appropriate text to the users.
* The returned dict should only contain (in principal) immutable data types as
  values and should only use strings as keys.
* Messaging to the players should be done in the command or script code not
  here.
* Raise a RuleError when something is tried which is obviously illegal.

Don't
=====
* Do not print anything or msg someone within the action code.

"""

from __future__ import division

import math

import game.gamesrc.world.dice as dice
from game.gamesrc.world.rule import RuleError

def dist(pos1, pos2):
    return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

class Action(object):

    def __init__(self, caller):
        self.caller = caller
        self.type_ = "COMPLEX_ACTION"
        self.name = "combat action"

    def msg(self, response):
        """
        Message all relevant persons.

        """
        msg_all = self.caller.ndb.combat_handler.msg_all
        msg_all("%s by %s." % (self.name, self.caller))


class Sprint(Action):

    def __init__(self, info_caller):
        super(Sprint, self).__init__(info_caller.char)
        self.info_caller = info_caller
        self.type_ = "COMPLEX_ACTION"
        self.name = "sprint"


    def apply(self):
        """
        Applies action. Is called by the
        game.gamesrc.world.rules.resolve_actions function.

        """
        response = dict()
        self.info_caller.db._combat_infos["consecutive_sprint_tests"] += 1
        if (self.info_caller.db._combat_infos["this_turn_sprint_tests"] + 1
            > max(1, math.ceil(self.caller.ndb.sr.skills.running / 2))):
            raise RuleError("only running / 2 (round up) sprint tests allowed")
        self.info_caller.db._combat_infos["this_turn_sprint_tests"] += 1
        if not "SPRINTING" in self.info_caller.status:
            self.info_caller.status.append("SPRINTING")
        if not "RUNNING" in self.info_caller.status:
            self.info_caller.status.append("RUNNING")
        # dp = dice_pool
        dice_pool = (self.caller.ndb.sr.skills.dice_pool("running") +
              self.info_caller.bonus("sprint"))
        # should be always true
        if "RUNNING" in self.info_caller.status:
            dice_pool += 2  # compensate for -2 in bonus
        hits, glitch = dice.roll_dice_pool(dice_pool, limit=self.caller.limit_physical)
        self.info_caller.db._combat_infos["hits_sprint"] += hits
        response["dp_fatigue"] = None  # as a flag
        if self.info_caller.db._combat_infos["consecutive_sprint_tests"] > 1:
            dp_fatigue = self.info_caller.db._combat_infos["consecutive_sprint_tests"]
            response_fatigue = self.caller.resist_fatigue(dp_fatigue)
            response.update(response_fatigue)
        response["dice_pool"] = dice_pool
        response["limit"] = self.caller.limit_physical
        response["hits"] = hits
        response["glitch"] = glitch

        return response


    def msg(self, response):
        """
        Message all relevant persons.

        """
        msg = self.caller.msg
        msg("You sprint %.1f meters further. (%i/%i[%i])" %
            (response["hits"] * self.caller.ndb.sr.attributes.sprint_increase,
            response["hits"],
            response["dice_pool"],
            response["limit"]))
        if response["dp_fatigue"]:
            msg("Through consecutive sprinting you suffer %i[%i] stun damage fatigue. (resist: %i/%i)" %
                (response["damage"],
                 response["damage_value"],
                 response["hits_fatigue"],
                 response["dp_fatigue"]))


class Move(Action):

    def __init__(self, info_caller, pos):
        super(Move, self).__init__(info_caller.char)
        self.info_caller = info_caller
        self.type_ = "MOVE_ACTION"
        self.name = "move"
        self.pos = pos


    def apply(self):
        """
        Applies action. Is called by the
        game.gamesrc.world.rules.resolve_actions function.

        """
        response = dict()
        response["at_maximum"] = False
        response["to_maximum"] = False
        already_moved = self.caller.ndb.combat_handler.ndb.already_moveds[self.caller.id]
        movement_max = self.info_caller.movement_max
        walk_max = self.info_caller.walk_max
        distance = dist(self.pos, self.caller.db.pos)
        # TODO check if line of movement is allowed
        # TODO trigger movement tests and questions for intercept action
        # TODO check if end position is allowed (within the room, not on
        # another character...)
        if distance + already_moved <= walk_max:
            new_pos = self.pos
            distance_moved = distance
        # Running
        elif (not "RUNNING" in self.info_caller.status
              and "FREE_ACTION_DONE" in self.info_caller.status):
            # not running yet and cannot start running, because FREE_ACTION is
            # not available
            # move to maximum walk distance
            distance_moved = walk_max - already_moved
            # move as far as you can
            scale = (distance_moved / distance)
            new_pos = (scale * (self.pos[0] - self.caller.db.pos[0]) +
                       self.caller.db.pos[0],
                       scale * (self.pos[1] - self.caller.db.pos[1]) +
                       self.caller.db.pos[1])
            response["to_maximum"] = True
        elif already_moved >= movement_max:
            distance_moved = 0
            new_pos = self.caller.db.pos
            response["at_maximum"] = True
        else:
            if not "RUNNING" in self.info_caller.status:
                self.info_caller.append("RUNNING")
                self.info_caller.append("FREE_ACTION_DONE")
            movement_left = movement_max - already_moved
            # move as far as you can
            scale = 1.0
            if distance > movement_left:
                scale = (movement_left / distance)
                response["to_maximum"] = True
            distance_moved = scale * distance
            new_pos = (scale * (self.pos[0] - self.caller.db.pos[0]) +
                       self.caller.db.pos[0],
                       scale * (self.pos[1] - self.caller.db.pos[1]) +
                       self.caller.db.pos[1])
        response["pos"] = new_pos
        self.caller.db.pos = new_pos
        self.caller.ndb.combat_handler.ndb.already_moveds[self.caller.id] += distance_moved
        return response


    def msg(self, response):
        """
        Message all relevant persons.

        """
        msg_all = self.caller.ndb.combat_handler.msg_all
        move_txt = "walks"
        if "SPRINTING" in self.info_caller.status:
            move_txt = "sprints"
        elif "RUNNING" in self.info_caller.status:
            move_txt = "runs"

        if response["at_maximum"]:
            msg_all("%s stands at (%.2f, %.2f) and cannot move any further." %
                    (self.caller, self.pos[0], self.pos[1]))
            return
        elif response["to_maximum"]:
            msg_all("%s %s to (%.2f, %.2f) and cannot move any further." %
                    (self.caller, move_txt, response["pos"][0],
                     response["pos"][1]))
            return
        else:
            msg_all("%s %s to (%.2f, %.2f)." %
                    (self.caller, move_txt, self.pos[0], self.pos[1]))


class CombatAction(Action):

    def __init__(self, info_attacker):
        super(CombatAction, self).__init__(info_attacker.char)
        self.info_attacker = info_attacker
        self.type_ = "COMPLEX_ACTION"
        self.name = "combat action"


    def apply(self):
        """
        Applies action. Is called by the
        game.gamesrc.world.rules.resolve_actions function.

        """

    def msg(self, response, attack_txt):
        """
        Message all relevant persons.

        """
        msg_all = self.caller.ndb.combat_handler.msg_all
        if response["out_of_range"]:
            msg_all("%s tries to %s %s but is out of range." %
                    (self.caller, attack_txt, self.target))
            return
        if response["net_hits"] <= 0:
            msg_all("%s misses %s. (attack: %i/%i[%i] defend: %i/%i)" %
                    (self.caller, self.target,
                     response["hits_attack"],
                     response["dp_attack"],
                     response["limit_attack"],
                     response["hits_defend"],
                     response["dp_defend"]))
            return
        else:
            msg_all("%s %ss %s with %i[%i] %s damage. (attack: %i/%i[%i] defend: %i/%i resist: %i/%i)" %
                    (self.caller, attack_txt, self.target,
                     response["damage"],
                     response["damage_value"],
                     response["damage_type"],
                     response["hits_attack"],
                     response["dp_attack"],
                     response["limit_attack"],
                     response["hits_defend"],
                     response["dp_defend"],
                     response["hits_resist"],
                     response["dp_resist"]))
            return


class Hit(CombatAction):

    def __init__(self, info_attacker, target_info):
        super(Hit, self).__init__(info_attacker)
        self.target_info = target_info
        self.target = target_info.char
        self.name = "hit"
        self.type_ = "COMPLEX_ACTION"


    def apply(self):
        """
        Applies action. Is called by the
        game.gamesrc.world.rules.resolve_actions function.

        """
        # dp = dice_pool
        response = dict()
        response["out_of_range"] = False
        if dist(self.caller.db.pos, self.target.db.pos) > 1:
            response["out_of_range"] = True
            return response
        dp_attack = (self.caller.ndb.sr.skills.dice_pool("unarmed_combat") +
                     self.info_attacker.bonus("unarmed_combat"))
        hits_attack, glitch_attack = dice.roll_dice_pool(dp_attack,
                                                         limit=self.caller.limit_physical)
        dp_defend, hits_defend, glitch_defend = self.target_info.defend()
        net_hits = hits_attack - hits_defend
        response["dp_attack"] = dp_attack
        response["limit_attack"] = self.caller.limit_physical
        response["hits_attack"] = hits_attack
        response["glitch_attack"] = glitch_attack
        response["dp_defend"] = dp_defend
        response["hits_defend"] = hits_defend
        response["glitch_defend"] = glitch_defend
        response["net_hits"] = net_hits
        if net_hits <= 0:
            return response
        response_resist = self.target.resist(
            self.caller.hit_damage + net_hits,
            self.caller.hit_damage_type)
        response.update(response_resist)
        return response


    def msg(self, response):
        super(Hit, self).msg(response, "hit")




# TODO move class to objects
class StandardAmmunition(object):

    def __init__(self, name="standard ammunition"):
        self.damage_value_modifier = 0
        self.armor_piercing_modifier = 0
        self.damage_type = None  # overwrites weapon damage type

# TODO move class to objects
class HeavyPistol(object):

    def __init__(self, name="heavy pistol"):
        self.name = name
        self.accuracy = 5
        self._damage_value = 8
        self._damage_type = "physical"
        self._armor_piercing = -1
        self.ammunition = StandardAmmunition()
        self.type_ = "PISTOL"
        self.category = "HEAVY_PISTOL"
        self.attribute = "pistols"

    @property
    def damage_value(self):
        return self._damage_value + self.ammunition.damage_value_modifier

    @property
    def damage_type(self):
        if self.ammunition.damage_type:
            return self.ammunition.damage_type
        else:
            return self._damage_type

    @property
    def armor_piercing(self):
        return self._armor_piercing + self.ammunition.armor_piercing_modifier

    def range_category(self, distance):
        if distance <= 5.5:
            return "SHORT"
        elif distance <= 20.5:
            return "MEDIUM"
        elif distance <= 40.5:
            return "LONG"
        elif distance <= 60.5:
            return "EXTREME"
        else:
            return "OUT_OF_RANGE"


class Shoot(CombatAction):

    def __init__(self, info_attacker, target_info):
        super(Shoot, self).__init__(info_attacker)
        self.target_info = target_info
        self.target = target_info.char
        self.weapon = HeavyPistol("Ares Predator V")
        self.name = "shoot"
        self.type_ = "SIMPLE_ACTION"


    @property
    def dp_attack_modifier(self):
        modifier = 0
        distance = dist(self.caller.db.pos, self.target.db.pos)
        range_category = self.weapon.range_category(distance)
        # distance modification
        # TODO environment modification
        if range_category == "SHORT":
            modifier -= 0
        elif range_category == "MEDIUM":
            modifier -= 1
        elif range_category == "LONG":
            modifier -= 3
        elif range_category == "EXTREME":
            modifier -= 6
        else:
            raise RuleError("weapon out of range")
        if "SPRINTING" in self.target_info.status:
            modifier -= 4
        elif "RUNNING" in self.target_info.status:
            modifier -= 2
        return modifier


    def apply(self):
        """
        Applies action. Is called by the
        game.gamesrc.world.rules.resolve_actions function.

        """
        # dp = dice_pool
        response = dict()
        response["out_of_range"] = False
        distance = dist(self.caller.db.pos, self.target.db.pos)
        self.caller.msg("You shoot from a distance of %.1f meter." % distance)
        if self.weapon.range_category(distance) == "OUT_OF_RANGE":
            response["out_of_range"] = True
            return response
        dp_attack = (self.caller.ndb.sr.skills.dice_pool(self.weapon.attribute) +
                     self.info_attacker.bonus(self.weapon.category) +
                     self.dp_attack_modifier)
        hits_attack, glitch_attack = dice.roll_dice_pool(dp_attack,
                                                         limit=self.weapon.accuracy)
        # TODO reduce amount of rounds
        # TODO handle recoil
        dp_defend, hits_defend, glitch_defend = self.target_info.defend()
        net_hits = hits_attack - hits_defend
        response["dp_attack"] = dp_attack
        response["hits_attack"] = hits_attack
        response["glitch_attack"] = glitch_attack
        response["limit_attack"] = self.weapon.accuracy
        response["dp_defend"] = dp_defend
        response["hits_defend"] = hits_defend
        response["glitch_defend"] = glitch_defend
        response["net_hits"] = net_hits
        if net_hits <= 0:
            return response
        response_resist = self.target.resist(self.weapon.damage_value +
                                             net_hits, self.weapon.damage_type,
                                             self.weapon.armor_piercing)
        response.update(response_resist)
        return response


    def msg(self, response):
        super(Shoot, self).msg(response, "shoot")


