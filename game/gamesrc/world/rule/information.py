#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Defines classes that store information in specific situations.

"""

import random

import game.gamesrc.world.dice as dice
from game.gamesrc.world.rule import RuleError


class CharacterCombatInformation(object):
    """
    Stores all the non persistent information needed only in combat like
    initiative and combat mali.

    """

    def __init__(self, character, db):
        self.char = character
        self.db = db
        if not self.db._combat_infos:
            self.db._combat_infos = {
                "number_defenses_this_turn": 0,
                "_initiative_dice": 1,
                "_initiative_rolled_dice": 0,
                "status": [],
                "counterspelling_pool":
                    character.ndb.sr.skills.counterspelling,
                "consecutive_sprint_tests": 0,
                "this_turn_sprint_tests": 0,
                "hits_sprint": 0
            }


    def __del__(self):
        del self.db._combat_infos


    # game flow (called by combat script)

    def new_combat_turn(self):
        """
        rolls new initiative and resets some counter.

        """
        self.db._combat_infos["hits_sprint"] = 0
        self.db._combat_infos["counterspelling_pool"] = self.char.ndb.sr.skills.counterspelling
        self.db._combat_infos["_initiative_rolled_dice"] = 0
        for ii in range(self.char.initiative_dice):
            self.db._combat_infos["_initiative_rolled_dice"] += dice.roll_die()
        # resolve initiative collisions by ERIC
        self.db._combat_infos["_initiative_rolled_dice"] += (
                0.01 * self.char.ndb.sr.attributes.edge
                + 0.0001 * self.char.ndb.sr.attributes.reaction
                + 0.000001 * self.char.ndb.sr.attributes.intuition
                + 0.0000001 * random.random())
        # TODO generalise in order to use more than one die and to use astral
        # initiative
        self.status_remove("FULL_DEFENSE")
        sustained_spells = self.char.db.sustained_spells
        for spell in sustained_spells:
            spell.combat_rounds_sustained += 1
        self.char.db.sustained_spells = [spell for spell in sustained_spells if
                                         not spell.done]


    def end_combat_turn(self):
        self.db._combat_infos["this_turn_sprint_tests"] = 0
        if not "SPRINTING" in self.status:
            self.db._combat_infos["consecutive_sprint_tests"] = 0
        self.status_remove("RUNNING")
        self.status_remove("SPRINTING")


    def new_initiative_pass(self):
        pass
        # TODO generalise in order to use more than one die and to use astral
        # initiative


    def end_initiative_pass(self):
        """
        remove 10 from initiative and reset ACTION_PHASE_DONE status.

        """
        if (10 >= self.initiative >= 1 and not "FULL_DEFENSE" in self.status):
            self.go_full_defense()
        self.db._combat_infos["_initiative_rolled_dice"] -= 10
        self.status_remove("ACTION_PHASE_DONE")
        self.status_remove("FREE_ACTION_DONE")
        self.status_remove("SIMPLE_ACTION_DONE")
        self.status_remove("SIMPLE_ACTION_DONE")
        self.status_remove("COMPLEX_ACTION_DONE")


    def new_action_phase(self):
        self.db._combat_infos["number_defenses_this_turn"] = 0


    def end_action_phase(self):
        self.status_remove("ATTACK_DONE")
        self.status.append("ACTION_PHASE_DONE")


    # properties

    @property
    def initiative(self):
        return (self.char.ndb.sr.attributes.reaction +
                self.char.ndb.sr.attributes.intuition +
                self.db._combat_infos["_initiative_rolled_dice"] +
                self.bonus("initiative"))


    @property
    def status(self):
        return self.db._combat_infos["status"]


    @property
    def movement_max(self):
        return (self.char.ndb.sr.attributes.agility *
                self.char.ndb.sr.attributes.run_rate +
                self.db._combat_infos["hits_sprint"] *
                self.char.ndb.sr.attributes.sprint_increase)


    @property
    def walk_max(self):
        return (self.char.ndb.sr.attributes.agility *
                self.char.ndb.sr.attributes.walk_rate)


    # utility

    def bonus(self, attribute):
        """
        Returns bonus that respects modifications due to the combat.

        """
        bonus = self.char.bonus(attribute)
        # for initiative only damage modifiers apply
        if attribute == "initiative":
            return bonus
        if attribute == "defense":
            bonus -= self.db._combat_infos["number_defenses_this_turn"]
        if "RUNNING" in self.status:
            bonus -= 2
        return bonus


    def status_remove(self, value):
        try:
            self.status.remove(value)
        except ValueError:
            pass


    # actions

    def remove_sustained_spell(self, spell):
        if "FREE_ACTION_DONE" in self.status:
            raise RuleError("Need a free action to remove sustained spell.")
        self.status.append("FREE_ACTION_DONE")
        spell.end_effect()
        self.char.db.sustained_spells.remove(spell)


    def go_full_defense(self):
        if "FULL_DEFENSE" in self.status:
            raise RuleError("{name} is in FULL_DEFENSE do not apply twice".format(name=self.name))
        if self.initiative < 1:
            raise RuleError("Initiative need to be above 0 in order to go into full defense.")
        self.db._combat_infos["_initiative_rolled_dice"] -= 10
        self.status.append("FULL_DEFENSE")


    def defend(self, limit=None, situational_modifier=0):
        """
        If a character defends herself, she rolls defend().

        Returns
        -------
        res = (dice_pool, hits, glitch)

        """
        dice_pool = (self.char.ndb.sr.attributes.reaction +
                     self.char.ndb.sr.attributes.intuition +
                     self.bonus("defense") +
                     situational_modifier)
        if "FULL_DEFENSE" in self.status:
            dice_pool += self.char.ndb.sr.attributes.willpower
        if dice_pool < 0:
            dice_pool = 0
        res = dice.roll_dice_pool(dice_pool, limit)
        self.db._combat_infos["number_defenses_this_turn"] += 1
        return (dice_pool, res[0], res[1])


    def resist_drain(self, spell):
        dice_pool = (self.char.ndb.sr.attributes.willpower +
                     self.char.ndb.sr.attributes.logic)
        resist_hits, glitch = dice.roll_dice_pool(dice_pool)
        drain = spell.drain
        drain_damage = max(0, drain - resist_hits)
        if spell.hits_cast > self.ndb.sr.attributes.magic:
            damage_type = "physical"
            self.char.damage_physical += drain_damage
        else:
            damage_type = "stun"
            self.char.damage_stun += drain_damage
        return (dice_pool, resist_hits, glitch, drain_damage, damage_type)

