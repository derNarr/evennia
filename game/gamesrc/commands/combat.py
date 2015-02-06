# /game/gamesrc/commands/combat.py

from ev import Command
from ev import CmdSet
from ev import default_cmds
from ev import create_script

import game.gamesrc.world.actions as actions


class CmdHit(Command):
    """
    hit an enemy

    Usage:
      hit <target>

    Strikes the given enemy with your current weapon.
    """
    key = "hit"
    aliases = ["strike", "slash"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        if not self.args:
            self.caller.msg("Usage: hit <target>")
            return
        target = self.caller.search(self.args)
        if not target:
            return
        combat_handler = self.caller.ndb.combat_handler
        ok = combat_handler.add_action(actions.Hit(
                    combat_handler.ndb.informations[self.caller.id],
                    combat_handler.ndb.informations[target.id]),
            self.caller)
        if ok:
            self.caller.msg("You add 'hit' to the combat queue")
        else:
            self.caller.msg("Something failed.")



class CmdShoot(Command):
    """
    shoot at an enemy

    Usage:
      shoot <target>

    Shoot at the enemy with your current weapon.
    """
    key = "shoot"
    aliases = []
    help_category = "combat"

    def func(self):
        "Implements the command"
        if not self.args:
            self.caller.msg("Usage: shoot <target>")
            return
        target = self.caller.search(self.args)
        if not target:
            return
        combat_handler = self.caller.ndb.combat_handler
        ok = combat_handler.add_action(actions.Shoot(
                    combat_handler.ndb.informations[self.caller.id],
                    combat_handler.ndb.informations[target.id]),
                self.caller)
        if ok:
            self.caller.msg("You add 'shoot' to the combat queue")
        else:
            self.caller.msg("Something failed.")


class CmdSprint(Command):
    """
    sprint and move therefore further

    Usage:
      sprint

    Sprint which takes a complex action and increases maximal run distance.
    """
    key = "sprint"
    aliases = []
    help_category = "combat"

    def func(self):
        "Implements the command"
        if self.args:
            self.caller.msg("Usage: sprint")
            return
        combat_handler = self.caller.ndb.combat_handler
        ok = combat_handler.add_action(actions.Sprint(
                    combat_handler.ndb.informations[self.caller.id]),
                self.caller)
        if ok:
            self.caller.msg("You add 'sprint' to the combat queue")
        else:
            self.caller.msg("Something failed.")



class CmdMove(Command):
    """
    move yourself

    Usage:
      move <x_pos>,<y_pos>

    Plans to move yourself to position x_pos,y_pos. Multiple uses possible. If
    movement exceeds walk_max, this action tries to use a free action in order
    to run. If you have no free action left, you walk as far as possible. If
    you can run, than you run as far as possible.

    """
    key = "move"
    aliases = []
    help_category = "combat"

    def func(self):
        "Implements the command"
        if not self.args:
            self.caller.msg("Usage: move <x_pos>,<y_pos>")
            return
        try:
            x_pos, y_pos = self.args.split(",")
            x_pos = float(x_pos)
            y_pos = float(y_pos)
        except ValueError:
            self.caller.msg("Usage: move <x_pos>,<y_pos>")
            return
        combat_handler = self.caller.ndb.combat_handler
        ok = combat_handler.add_action(actions.Move(
                    combat_handler.ndb.informations[self.caller.id],
                    pos=(x_pos, y_pos)),
            self.caller)
        if ok:
            self.caller.msg("You add 'move' to the combat queue")
        else:
            self.caller.msg("Something failed.")



class CmdReview(Command):
    """
    review your planned actions

    Usage:
      review

    Reviews your planned actions.
    """
    key = "review"
    aliases = []
    help_category = "combat"

    def func(self):
        "Implements the command"
        if self.args:
            self.caller.msg("Usage: review")
            return
        combat_handler = self.caller.ndb.combat_handler
        for ii, action in enumerate(
            combat_handler.ndb.planned_actions[self.caller.id]):
            self.caller.msg("%2i. %.8s (%s)" % (ii + 1, action.name, action.type_))



class CmdCommit(Command):
    """
    commit your planned actions

    Usage:
      commit

    Commits your planned actions. Your might ``review`` your actions first.
    """
    key = "commit"
    aliases = ["c"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        if self.args:
            self.caller.msg("Usage: commit")
            return
        combat_handler = self.caller.ndb.combat_handler
        combat_handler.commit(self.caller)
        combat_handler.at_repeat("commit")



class CmdClear(Command):
    """
    clear all your planned actions

    Usage:
      clear

    Clears your planned actions. Your might ``review`` your actions first.
    """
    key = "clear"
    aliases = ["revert"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        if self.args:
            self.caller.msg("Usage: clear")
            return
        combat_handler = self.caller.ndb.combat_handler
        combat_handler.ndb.planned_actions[self.caller.id] = []
        self.caller.msg("All planned actions cleared.")



class CmdRetreat(Command):
    """
    retreat from combat

    Usage:
      retreat

    Retreats immediately from combat.
    """
    key = "retreat"
    aliases = ["r"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        if self.args:
            self.caller.msg("Usage: retreat")
            return
        combat_handler = self.caller.ndb.combat_handler
        combat_handler.remove_character(self.caller)
        combat_handler.at_repeat("retreat")



class CmdStatus(Command):
    """
    Show status of combat

    Usage:
      status [<target>]

    Show overall status or status of single target.
    """
    key = "status"
    aliases = ["s"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        combat_handler = self.caller.ndb.combat_handler
        if not self.args:
            combat_handler.status(self.caller)
            return
        target = self.caller.search(self.args)
        if not target:
            combat_handler.status(self.caller)
            return
        combat_handler.status(self.caller, target)


class CmdHelp(Command):
    """
    help for combat

    Usage:
      help

    Shows help message for combat commands.
    """
    key = "help"
    aliases = []
    help_category = "combat"

    def func(self):
        self.caller.msg(
            """
            Combat:
             1. put actions in your planning cue by calling them (e. g. ``hit`` / ``shoot <target>``)
             2. ``review`` your planned actions
             3. ``commit`` them

            ``retreat`` if you are to heavily wounded
            """)



class CombatCmdSet(CmdSet):
    key = "combat_cmdset"
    mergetype = "Replace"
    priority = 10
    no_exits = True

    def at_cmdset_creation(self):
        self.add(CmdMove())
        self.add(CmdSprint())
        self.add(CmdHit())
        self.add(CmdShoot())
        self.add(CmdClear())
        self.add(CmdReview())
        self.add(CmdCommit())
        self.add(CmdRetreat())
        self.add(CmdStatus())
        self.add(CmdHelp())
        self.add(default_cmds.CmdPose())
        self.add(default_cmds.CmdSay())



class CmdAttack(Command):
    """
    initiates combat

    Usage:
      attack <target>

    This will initiate combat with <target>. If <target> is
    already in combat, you will join the combat.
    """
    key = "attack"
    help_category = "General"

    def func(self):
        "Handle command"
        if not self.args:
            self.caller.msg("Usage: attack <target>")
            return
        target = self.caller.search(self.args)
        if not target:
            return
        # set up combat
        if target.ndb.combat_handler:
            # target is already in combat - join it
            target.ndb.combat_handler.add_character(self.caller)
            target.ndb.combat_handler.msg_all("%s joins combat!" % self.caller)
        else:
            # create a new combat handler
            chandler = create_script("game.gamesrc.scripts.combat_handler.CombatHandler")
            chandler.add_character(self.caller)
            chandler.add_character(target)
            self.caller.msg("You attack %s! You are in combat." % target)
            target.msg("%s attacks you! You are in combat." % self.caller)

