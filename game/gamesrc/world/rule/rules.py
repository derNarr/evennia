#!/usr/bin/env python
# -*- encoding: utf-8 -*-

class RuleError(Exception):
    pass


def resolve_actions(combat_handler, actions, character):
    info_char = combat_handler.ndb.informations[character.id]

    sprint = [action for action in actions if action.name == "sprint"]
    if sprint:
        response = sprint[0].apply()  # sets status to "RUNNING" and "SPRINTING"
        sprint[0].msg(response)
        actions = [action for action in actions if action.name != "sprint"]
    else:
        positions = [action.pos for action in actions if action.name == "move"]
        dist = 0
        start_pos = character.db.pos
        for pos in positions:
            dist += ((pos[0] - start_pos[0]) ** 2
                    + (pos[1] - start_pos[1]) ** 2 ) ** 0.5
            start_pos = pos
        if (dist > info_char.walk_max
                and not "RUNNING" in info_char.status
                and not "SPRINTING" in info_char.status):
            info_char.status.append("RUNNING")

    for action in actions:
        response = action.apply()
        action.msg(response)

