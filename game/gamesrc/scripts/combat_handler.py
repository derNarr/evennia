#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
from ev import Script
from game.gamesrc.world.rule import (resolve_actions,
                                     CharacterCombatInformation)

class CombatHandler(Script):
    """
    This implements the combat handler.

    """

    # standard Script hooks

    def at_script_creation(self):
        "Called when script is first created"

        self.key = "combat_handler_%i" % random.randint(1, 1000)
        self.desc = "handles combat"
        self.interval = 6
        self.start_delay = True
        self.persistent = True

        # seconds to be added to remaining_time after
        #  1. a commit of actions
        #  2. answering a yes / no question
        self.db.base_time = 120  # seconds
        self.db.add_time_commit = 12  # seconds
        self.db.add_time_question = 6  # seconds

        # some global variables
        self.db.start_time = time.time()
        self.db.n_turns_done = -1
        self.db.n_passes_done = 0

        # store all combatants
        self.db.characters = {}
        # store remaining time for each combatant
        self.db.remaining_times = {}
        # store if combatant has committed his actions
        self.db.commits = {}

        # non-pickable objects because of back-references
        # store all planned actions
        self.ndb.planned_actions = {}
        # stores instance of CharacterCombatInformation for each combatant
        self.ndb.informations = {}
        # stores distance a character is moved in this combat turn
        self.ndb.already_moveds = {}


    def _init_character(self, character):
        """
        This initializes handler back-reference and combat cmdset on a
        character
        """
        dbref = character.id
        self.ndb.informations[dbref] = CharacterCombatInformation(character,
                                                                  character.db)
        self.ndb.planned_actions[dbref] = []
        self.ndb.already_moveds[dbref] = 0.0
        character.msg("You have no planned actions.")
        character.ndb.combat_handler = self
        character.cmdset.add("game.gamesrc.commands.combat.CombatCmdSet")


    def _cleanup_character(self, character):
        """
        Remove character from handler and clean it of the back-reference and
        cmdset.
        """
        dbref = character.id
        del self.db.characters[dbref]
        del self.db.remaining_times[dbref]
        del self.ndb.planned_actions[dbref]
        del self.db.commits[dbref]
        del self.ndb.already_moveds[dbref]
        del self.ndb.informations[dbref]
        del character.ndb.combat_handler
        character.cmdset.delete("game.gamesrc.commands.combat.CombatCmdSet")


    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this combat handler to all
        characters as well as re-assign the cmdset. We also need to restore the
        CharacterCombatInformation.
        """
        self.ndb.informations = {}
        self.ndb.planned_actions = {}
        self.ndb.already_moveds = {}
        for character in self.db.characters.values():
            self._init_character(character)


    def at_stop(self):
        "Called just before the script is stopped/destroyed."
        if not self.db.characters:
            return
        for character in list(self.db.characters.values()):
            # note: the list() call above disconnects list from database
            self._cleanup_character(character)


    def at_repeat(self, *args):
        """
        This is called every self.interval seconds.

        We let this method take optional arguments (using *args) so we can separate
        between the timeout (no argument) and the controlled turn-end
        where we send an argument.
        """
        # after start up
        if self.db.n_turns_done == -1:
            while not self.ndb.informations:
                time.sleep(0.1)
            time.sleep(0.3)
            self.db.n_turns_done = 0
            self.new_turn()
            self.new_pass()
            return
        if not self.ndb.informations:
            if args:
                # recursive call
                return
            self.stop()
        char = self.get_moving_character()
        if not char:
            return
        # all dead?
        if all([set.intersection(set(chummer.db.status),
                                 set(("UNCONSCIOUS", "DYING", "DEAD")))
                for chummer in self.db.characters.values()]):
            if args:
                # recursive call
                return
            self.stop()
        dbref = char.id
        info = self.ndb.informations[dbref]

        if info.initiative < 1:
            self.end_pass()
            self.end_turn()
            self.new_turn()
            self.new_pass()
            return

        if "ACTION_PHASE_DONE" in info.status:
            self.end_pass()
            self.new_pass()
            return

        # only reduce remaining_time when at_repeat is called after
        # self.interval seconds (no *args)
        if (not args and not self.db.commits[dbref] and
                    self.db.remaining_times[dbref] > 0):
            self.db.remaining_times[dbref] -= self.interval
            if self.db.remaining_times[dbref] < 24:
                char.msg("Only %i seconds left to commit." %
                         self.db.remaining_times[dbref])
            return

        if args and args[0] in ("recursive", "start"):
            char.msg("It is your turn now. You have %i seconds left to commit."
                     % self.db.remaining_times[dbref])
            self.status(char)

        # commited?
        if not self.db.commits[dbref]:
            return

        if self.db.remaining_times[dbref] < 0:
            self.db.remaining_times[dbref] = 0
            char.msg("You are out of time. You are forced to move.")

        # new action phase of char starts here
        info.new_action_phase()  # in order to reset some counters
        resolve_actions(self, self.ndb.planned_actions[dbref], char)
        info.end_action_phase()

        self.db.remaining_times[dbref] += self.db.add_time_commit
        self.ndb.planned_actions[dbref] = []
        self.db.commits[dbref] = False
        # action phase ends here

        # recursive call
        self.at_repeat("recursive")


    # Combat-handler methods

    # utility

    def add_character(self, character):
        "Add combatant to handler"
        # do the following todo somewhere else!
        # TODO delay character if she joins later for ((time.time() -
        # self.db.start_time) // 3 - self.db.n_turns_done) combat turns.

        # put character at a random position in a 40 x 40 meter square
        # TODO improve initial placement
        dbref = character.id
        character.db.pos = (random.randint(0, 40), random.randint(0, 40))
        self.db.characters[dbref] = character
        self.db.remaining_times[dbref] = self.db.base_time
        self.db.commits[dbref] = False
        del character.ndb.combat_handler
        del character.db._combat_infos
        self._init_character(character)


    def remove_character(self, character):
        "Remove combatant from handler"
        self.msg_all("%s retreats from combat." % character.name)
        if character.id in self.db.characters:
            self._cleanup_character(character)
        if not self.db.characters:
            # if we have no more characters in battle, kill this handler
            self.stop()


    def msg_all(self, message):
        "Send message to all combatants"
        for character in self.db.characters.values():
            character.msg(message)


    def status(self, character, target=None):
        "Print current status to character."
        infos = self.ndb.informations.values()
        if not infos:
            character.msg("No information available yet.")
            return None
        infos.sort(key=lambda info: info.initiative, reverse=True)

        if target is None:
            # print short summary
            character.msg("---------  ---  -----  --------  -----------  ----")
            character.msg("Character  Ini  Moved  Dam(s/p)  Position     Time")
            character.msg("---------  ---  -----  --------  -----------  ----")
            for info in infos:
                character.msg("%9s  %3i  %5s   (%2i/%2i)  %5.1f,%5.1f  %4i  %s %s" % (
                    info.char.name,
                    round(info.initiative),
                    "X" if ("ACTION_PHASE_DONE" in info.status) else "",
                    info.char.damage_stun, info.char.damage_physical,
                    info.char.db.pos[0], info.char.db.pos[1],
                    self.db.remaining_times[info.char.id],
                    " ".join(info.char.db.status),
                    " ".join(info.status)))
            character.msg("---------  ---  -----  --------  -----------  ----")
            return
        tmp = [info for info in infos if info.char == target]
        if not tmp:
            return
        target_info = tmp[0]
        target = target_info.char
        character.msg("== {name} ==\n".format(name=target.name) +
          "Stun {damage_stun}/{damage_stun_max} ".format(
              damage_stun=target.damage_stun,
              damage_stun_max=target.damage_stun_max) +
          "Physical {damage_physical}/{damage_physical_max}  ".format(
              damage_physical=target.damage_physical,
              damage_physical_max=target.damage_physical_max) +
          "Ini {ini}  ".format(ini=round(target_info.initiative, 2)) +
          "Bonus(ini) {bonus}  ".format(bonus=target_info.bonus("initiative")) +
          "Position %3.1f,%3.1f  " % target.db.pos +
          "Status: " + " ".join(target_info.status) +
          " " + " ".join(target.db.status))
        character.msg("Attr: B %i  A %i  R %i  S %i  W %i  L %i  I %i  C %i  E %i  ESS %.1f" %
                      (target.ndb.sr.attributes.body,
                       target.ndb.sr.attributes.agility,
                       target.ndb.sr.attributes.reaction,
                       target.ndb.sr.attributes.strength,
                       target.ndb.sr.attributes.willpower,
                       target.ndb.sr.attributes.logic,
                       target.ndb.sr.attributes.intuition,
                       target.ndb.sr.attributes.charisma,
                       target.ndb.sr.attributes.edge,
                       target.ndb.sr.attributes.essence))
        character.msg("Skills: unarmed_combat %i  running %i" %
                      (target.ndb.sr.skills.unarmed_combat,
                       target.ndb.sr.skills.running))
        character.msg("Misc: armor %i" %
                      (target.db.armor))



    def add_action(self, action, character, pos=None):
        """
        Called by combat commands to register an action with the handler.

        Parameters
        ----------
        action : Action
        character : Character
            the character performing the action
        pos : int or None
            None inserts action at the end

        planned actions are stored in a dictionary keyed to each character,
        each of which holds a list actions.

        Returns
        -------
        True : if action added successfully
        False : if action is not added

        NOTE: use exception instead?
        """
        dbref = character.id

        if self.db.commits[dbref]:
            return False

        # NOTE: this checks might belong in the rule module
        types = [ac.type_ for ac in self.ndb.planned_actions[dbref]]

        if "COMPLEX_ACTION" in types or len([t for t in types if t ==
                                             "SIMPLE_ACTION"]) == 2:
            # only movement and free actions might be allowed
            if action.type_ in ("COMPLEX_ACTION", "SIMPLE_ACTION"):
                return False

        if len([t for t in types if t == "SIMPLE_ACTION"]) == 1:
            if action.type_ == "COMPLEX_ACTION":
                return False

        if "FREE_ACTION" in types:
            if action.type_ == "FREE_ACTION":
                return False

        # movement will not be checked -- the character moves as far as she can
        # run or sprint

        if pos is None:
            self.ndb.planned_actions[dbref].append(action)
        else:
            self.ndb.planned_actions[dbref].insert(pos, action)
        return True


    def commit(self, character):
        """
        Commits the planned actions of the character.

        """
        self.db.commits[character.id] = True


    def get_moving_character(self):
        """
        Return character that has his turn.

        """
        infos = self.ndb.informations.values()
        if not infos:
            return None
        infos.sort(key=lambda info: info.initiative, reverse=True)
        for info in infos:
            if "ACTION_PHASE_DONE" in info.status:
                continue
            if set.intersection(set(info.char.db.status), set(("UNCONSCIOUS",
                                                               "DYING",
                                                               "DEAD"))):
                continue
            return info.char
        return infos[0].char


    # game flow

    def new_pass(self):
        """
        Start a new initiative pass.

        """
        for char in self.db.characters.values():
            self.ndb.informations[char.id].new_initiative_pass()
        self.msg_all("%i. initiative pass begins..." % (self.db.n_passes_done + 1))
        for char in self.db.characters.values():
            self.status(char)
        self.at_repeat("start")


    def end_pass(self):
        """
        End an initiative pass.

        """
        self.db.n_passes_done += 1
        for char in self.db.characters.values():
            self.ndb.informations[char.id].end_initiative_pass()


    def new_turn(self):
        """
        Start a new combat turn.

        """
        self.db.n_passes_done = 0
        for char in self.db.characters.values():
            self.ndb.informations[char.id].new_combat_turn()
            self.ndb.already_moveds[char.id] = 0.0
        self.msg_all("%i. combat turn begins..." % (self.db.n_turns_done + 1))


    def end_turn(self):
        """
        Ends a combat turn. Resets some counters etc.

        """
        self.db.n_turns_done += 1
        for char in self.db.characters.values():
            self.ndb.informations[char.id].end_combat_turn()

