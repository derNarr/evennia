======
Combat
======

General
=======
Combat should consist of three phases:

1. In the *initiating phase* combatants engage into combat. There must be a
   time frame where all characters that engage into combat are handled as they
   would be in combat from the first round on. All characters in the
   contributing room(s) should be automatically added to the combat. At the end
   of this phase, the in-game start time of the combat is saved, round based
   combat mode is started, and in-game time runs much slower know for all
   combatants. All combatants might be teleported into a separate instance of
   the room(s).

2. *Combat phase* turn based combat. When a combatant want to join the combat
   the difference between current time in the combat time frame and the global
   time of the main instance is calculated. The new combatant must wait until
   the combat time reaches the global time stamp she was joining.

3. *Finishing phase* all concious combatants can now finish the combat by
   cleaning up the room, searching the fallen, and retreating from combat to a
   safe place. The finishing phase is still in the time frame of the combat.
   After the finishing phase ends all combatants are teleported back into the
   main instance and all clocks are synchronized.


Initiating phase
================

Minimal
-------
* set position of characters

Later
-----
* surprise tests
* which information is available (perception tests and stealth test)

Combat phase
============
Use a fisher time system 120 seconds + 6 seconds per commit + 3 seconds per
binary decision.

Minimal
-------
* combat sticks to a room (i. e. room is in combat mode)
* turn based
* combat turns
* initiative passes
* move
* shoot
* hit
* commit
* retreat

* resolve end of combat (unconciousness, death, retreat)

Later
-----
* characters later entering the room join the combat in (current_time -
  start_time) // 3 - played_combat_turns. They get an information how many
  combat turns they need to wait.
* review
* revert [move|actions|all (default)]
* draw
* ready


Finishing phase
===============

Later
-----
* search / loot fallen

