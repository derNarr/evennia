#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Implements tests with dice for Shadowrun 5.

"""

import random

def roll_die():
    """
    roll a six sided die.

    """
    return random.randint(1, 6)


def roll_dice_pool(pool, limit=None, verbose=False):
    """
    roll a dice pool and return hits and if a glitch occurs glitch=(None,
    "GLITCH", "CRITICAL_GLITCH")

    """
    dice = [roll_die() for die in range(pool)]
    hits = len([die for die in dice if die >= 5])
    ones = len([die for die in dice if die == 1])
    if verbose:
        print("Würfelwurf: " + " ".join([str(die) for die in dice]))
        print("Erfolge: " + str(hits))
    glitch = None
    if ones > pool/2 and hits > 0:
        glitch = "GLITCH"
    if ones > pool/2 and hits == 0:
        glitch = "CRITICAL_GLITCH"
    if not limit is None:
        hits = min(limit, hits)
    return (hits, glitch)


def success_test(test, character, specialization=None):
    """
    Parameters
    ----------
    test : string
        of the form "skill + attribute [limit] (threshold) + modifier"
    character : Character
        character which probes this test

    Returns
    -------
    (number_of_net_hits, number_of_hits, glitch) : (int, int, unicode)
            glitch is one of "no_glitch", "glitch", "critical_glitch".
    """
    skill = test.split("+")[0].strip()
    attribute = test.split("+")[1].split("[")[0].strip()
    limit = float(test.split("+")[1].split("[")[1].split("]")[0].strip())
    threshold = int(test.split("+")[1].split("]")[1].replace("(","").replace(")","").strip())
    modifier = int(test.split("+")[2].strip())
    dice_pool = getattr(character, skill) + getattr(character, attribute) + modifier
    if specialization in character.specializations[skill]:
        dice_pool += 2
    hits = 0
    ones = 0
    for i in range(dice_pool):
        pips = roll_die()
        if pips == 1:
            ones += 1
        if pips in (5, 6):
            hits += 1
    glitch = None
    if ones > dice_pool / 2:
        glitch = "GLITCH"
    if hits == 0 and glitch == "GLITCH":
        glitch = "CRITICAL_GLITCH"
    net_hits = hits - threshold
    if net_hits > limit:
        net_hits = limit
    return (net_hits, hits, glitch)


def opposed_test(test, attacker, defender):
    """
    Parameters
    ----------
    test : string
        of the form "skill + attribute [limit] + modifier vs. skill + attribute [limit] + modifier"
    attacker : Character
    defender : Character

    Returns
    -------
    (net_hits_attacker, glitch_attacker, glitch_defender) : (int, string, string)
            glitch is one of "no_glitch", "glitch", "critical_glitch".

    """
    raise NotImplementedError()
    test_attacker, test_defender = test.split("vs.")
    # add "fake" threshold
    #skill_attacker
    #attribute_attacker
    #limit_attacker
    #skill_defender
    #attribute_defender
    #limit_defender
    pass


def extended_test(start_pool, limit, target_hits):
    """
    TODO

    """
    pool = start_pool
    hits = 0
    duration = 0
    while pool > 1:
        duration += 1
        hit, glitch = roll_dice_pool(pool, limit=limit)
        hits += hit
        if glitch == "GLITCH":
            hits -= roll_die()
        if hits <= 0 or glitch == "CRITICAL_GLITCH":
            hits = "FAIL"
            break
        if hits >= target_hits:
            hits = "SUCCESS"
            break
        pool -= 1
    return (hits, duration)


if __name__ == "__main__":
    while True:
        response = input("Wie viele Würfel sollen geworfen werden? ('exit' zum Beenden)\n")
        if response == "exit":
            break
        try:
            response = int(response)
        except ValueError:
            print("keine Zahl")
            continue
        dice = [roll_die() for die in range(response)]
        print("Würfe: " + " ".join([str(die) for die in dice]))
        hits = len([die for die in dice if die >= 5])
        print("Erfolge: " + str(hits))
        ones = len([die for die in dice if die == 1])
        if ones > response/2 and hits > 0:
            print("Ein Glitch :/")
        if ones > response/2 and hits == 0:
            print("Oh nein! Ein Critical Glitch :(")
        print("\n")

