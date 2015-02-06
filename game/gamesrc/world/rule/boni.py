#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Objects handling SR5 boni.

"""

class Boni(object):

    def __init__(self):
        self._boni = list()
        # list that stores the boni with
        #   (value [int], applied_to [str], bonus_type [str], source [id])

    def add(self, applied_to, value, bonus_type, source):
        self._boni.append((applied_to, value, bonus_type, source))

    def remove(self, source):
        self._boni = [bonus for bonus in self._boni if bonus[3] != source]

    def get(self, attribute):
        boni_by_type = dict()
        for applied_to, value, bonus_type, source in self._boni:
            if applied_to != attribute:
                continue
            if bonus_type in boni_by_type.keys():
                boni_by_type[bonus_type].append(value)
            else:
                boni_by_type[bonus_type] = [value,]  # list
        bonus = 0
        for boni in boni_by_type.values():
            # boni of the same type don't stack -- take the best one
            bonus += max(boni)
        return min(4, bonus)

