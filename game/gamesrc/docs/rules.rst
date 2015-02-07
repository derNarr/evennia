=====
Rules
=====
This document give a brief overview over the rule system of SR duel.

Basic Concepts
==============

success test
------------
(dice_pool, limit, threshold) -> (outcome [critical_glitch, glitch, failure,
success], hits, net_hits)

opposed test
------------
(dice_pool_actor, limit_actor, dice_pool_defender, limit_defender)
-> (outcome_actor [critical_glitch, glitch, failure, success], outcome_defender
[critical_glitch, glitch, failure, success], hits_actor, hits_defender,
net_hits)

extended test
-------------
(dice_pool, limit, threshold, interval) -> (outcome [critical_glitch, glitch,
failure, success], hits)

.. note::

    Hits are accumulated over several successive tests. Each successive test
    decreases its dice_pool by one. If the accumulated hits reach or exceed the
    threshold the test is successful. Otherwise the test is a failure. Glitch
    reduces accumulated hits by 1d6, if the accumulated hits fall below zero
    the extended test fails. Critical_glitch leads immediately to failure. If
    an extended test fails by a critical_glitch all spend resources are lost.
    If it fails naturally all spend resources are lost except for material
    expenses which can be recovered by 50%.

    Extended tests can be paused for a time span of LOG * interval.

trying again
------------
cumulative dice_pool_modification of -2

.. note::

    This dice_pool_modification can be reset after a time interval of (12 -
    WIL) * interval or a day of rest which grants edge refill, whichever is
    longer.

    This only applies for tests corresponding to the same task. This task
    should normally end after one success.

team work test
--------------
1. determine leader
#. assistants roll skill + attribute [limit] with at least one hit limit of the
   leader increases by 1, additionally each hit adds +1 to the leaders
   dice_pool.
#. leader rolls modified test with a maximal dice_pool_modification equal to
   the leader's skill rating or the higher attribute, if the test consists of
   two attributes. The leaders limit has a maximum at doubled original limit.

.. note::

    Assistant's glitch leads to no modification in the limit but still adds to
    the dice_pool. Assistant's critical_glitch leads to no increase of the
    leader's limit of any assistant. The dice_pool is still modified.
    Additionally the effects of a critical_glitch takes place.


=========   ==========================================
Concept     Type
=========   ==========================================
dice_pool   int
limit       int or infinity
threshold   int
outcome     critical_glitch, glitch, failure, success
hits        int (limit applied)
net_hits    int (can be negative)
=========   ==========================================


Open Questions
==============

* Can one combine full defense and e. g. dodge in order to get REA + INT + WIL
  + Gymnastics [Physical]

