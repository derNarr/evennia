

from game.gamesrc.world.rule import RuleError


class Sr5Attributes(object):
    ATTRIBUTES = ("body",
                  "agility",
                  "reaction",
                  "strength",
                  "willpower",
                  "logic",
                  "intuition",
                  "charisma",
                  "edge",
                  "essence",
                  "magic",
                  "resonance",
                  "body_max",
                  "agility_max",
                  "reaction_max",
                  "strength_max",
                  "willpower_max",
                  "logic_max",
                  "intuition_max",
                  "charisma_max",
                  "edge_max",
                  "essence_max",
                  "magic_max",
                  "resonance_max",

                  # misc
                  "walk_rate",
                  "run_rate",
                  "sprint_increase")

    def __init__(self, db):
        """
        When an _attributes object in the db exists, the db will not be initialized.

        """
        self.db = db
        if not self.db._attributes:
            self.db._attributes = dict()
            for attribute in self.ATTRIBUTES:
                if attribute[-4:] == "_max":
                    self.db._attributes[attribute] = 6
                else:
                    self.db._attributes[attribute] = 3
            self.db._attributes["edge"] = 1
            self.db._attributes["essence"] = 6
            self.db._attributes["magic"] = 0
            self.db._attributes["resonance"] = 0

            self.db._attributes["walk_rate"] = 2
            self.db._attributes["run_rate"] = 4
            self.db._attributes["sprint_increase"] = 1


    def __getattr__(self, name):
        if name in self.ATTRIBUTES:
            return self.db._attributes[name] + self.bonus(name)
        else:
            raise AttributeError()


    def __setattr__(self, name, value):
        if name in self.ATTRIBUTES:
            self.db._attributes[name] = value
        else:
            object.__setattr__(self, name, value)


    def bonus(self, name):
        # TODO
        return 0


    def add_bonus(self, name, bonus, type_, source):
        # TODO
        pass


    def remove_bonus(self, source):
        # TODO
        pass



class Sr5Skills(object):
    # dict might be problematic because it is mutable
    # key: name, value (attribute, defaulting, group)
    # TODO incomplete
    BASE_SKILLS = {
        "archery": ("agility", True, ""),
        "automatics": ("agility", True, "firearms"),
        "blades": ("agility", True, "close_combat"),
        "clubs": ("agility", True, "close_combat"),
        "heavy_weapon": ("agility", True, ""),
        "longarms": ("agility", True, "firearms"),
        "pistols": ("agility", True, "firearms"),
        "throwing_weapons": ("agility", True, ""),
        "unarmed_combat": ("agility", True, "close_combat"),
        # TODO some missing
        "gymnastics": ("agility", True, "athletics"),
        "perception": ("intuition", True, ""),
        "running": ("strength", True, "athletics"),
        "sneaking": ("agility", True, "stealth"),
        "survival": ("willpower", True, "outdoors"),
        "tracking": ("intuition", True, "outdoors"),
        # TODO some missing
        "assensing": ("intuition", False, ""),
        "astral_combat": ("willpower", False, ""),
        "banishing": ("magic", False, "conjuring"),
        "binding": ("magic", False, "conjuring"),
        "counterspelling": ("magic", False, "sorcery"),
        "spellcasting": ("magic", False, "sorcery"),
        "summoning": ("magic", False, "conjuring"),
        "compiling": ("resonance", False, "tasking"),
        "decompiling": ("resonance", False, "tasking"),
        "registering": ("resonance", False, "tasking"),
        # TODO some missing
        "computer": ("logic", True, "electronics"),
        "cybercombat": ("logic", True, "cracking"),
        "demolitions": ("logic", True, ""),
        "electronic warfare": ("logic", False, "cracking"),
        "first_aid": ("logic", True, "biotech"),
        "hacking": ("logic", True, "cracking"),
        "hardware": ("logic", False, "electronics"),
        "medicine": ("logic", False, "biotech"),
    }


    def __init__(self, db, attributes):
        """
        When an _skill_infos object in the db exists, the db will not be
        initialized.

        """
        object.__setattr__(self, "db", db)  # because of custom __setattr__
        object.__setattr__(self, "attributes", attributes)  # because of custom __setattr__
        if not self.db._skill_infos:
            self.db._skill_infos = self.BASE_SKILLS
            self.db._skill_ratings = dict()
            self.db._skill_groups = dict()
            self.db._skill_specializations = dict()
            for skill in self.db._skill_infos.keys():
                self.db._skill_ratings[skill] = 0
            for group in set([value[2] for value in self.BASE_SKILLS.values()]):
                if group == "":
                    continue
                self.db._skill_groups[group] = 0


    def __getattr__(self, name):
        try:
            return self.db._skill_ratings[name]
        except KeyError:
            raise AttributeError("%s has no attribute %s" % (type(self), name))


    def __setattr__(self, name, value):
        try:
            self.db._skill_ratings[name] = value
        except KeyError:
            object.__setattr__(self, name, value)


    def dice_pool(self, skill, specialization=None):
        """
        Returns dice pool for skill. Takes care of defaulting. Raise SkillError
        if skill test is not possible.

        """
        dice_pool = 0
        try:
            attr, default, group = self.db._skill_infos[skill]
        except KeyError:
            raise ValueError("skill '%s' not found" % skill)
        dice_pool += self.attributes.__getattr__(attr)
        if group and self.db._skill_groups[group] > 0:
            dice_pool += self.db._skill_groups[group]
            return dice_pool
            # skill groups do not allow specializations
        rating = self.db._skill_ratings[skill]
        if rating == 0:
            if default:
                dice_pool -= 1
                return dice_pool
            else:
                raise RuleError("You cannot default %s." % skill)
        dice_pool += rating
        if specialization:
            try:
                if specialization in self.db._skill_specializations[skill]:
                    dice_pool += 2
            except KeyError:
                pass
        return dice_pool


    def add(self, skill, attribute, defaulting=False, group=""):
        """
        Adds custom skill to character.

        skill : string
        attribute : string
        defaulting : bool
        group : string

        """
        self.db._skill_infos[skill] = (attribute, defaulting, group)
        self.db._skill_ratings[skill] = 0
        if group and group not in self.db._skill_groups.keys():
            self.db._skill_groups[group] = 0



class Sr5Character(object):

    def __init__(self, db):
        """
        If the objects in the db exists, theses objects will not be
        initialized.

        """
        self.db = db

        self.attributes = Sr5Attributes(self.db)
        self.skills = Sr5Skills(self.db, self.attributes)

        # TODO armor, karma, nuyen, damage??


