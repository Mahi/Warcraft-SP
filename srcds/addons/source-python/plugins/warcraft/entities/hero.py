"""A module with the :class:`Hero` base class for all heroes."""

# Python 3 imports
import collections
import math

# Warcraft imports
from warcraft.entities.entity import Entity
import warcraft.listeners

__all__ = (
    'Hero',
)


class _HeroMeta(type):
    """Metaclass for handling hero classes' skills.

    Adds a :attr:`skill_classes` list to all hero classes for storing
    the hero's skills, and `passive_classes` for storing the passives.

    Also implements :meth:`skill` and :meth:`passive` decorators to
    easily add skills and passives to the hero.
    """

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.skill_classes = []
        cls.passive_classes = []

    def skill(cls, skill_class):
        """Add a skill class to the hero class's :attr:`skill_classes`.

        Designed to be used as a decorator:

        .. code-block:: python

            class MyHero(Hero):
                ...

            @MyHero.skill
            class MySkill(Skill):
                ...

        :param type skill_class:
            Skill to add to the hero's skills
        """
        if skill_class in cls.skill_classes:
            raise ValueError(
                "Skill class {0} already added to a hero.".format(skill_class))
        cls.skill_classes.append(skill_class)
        return skill_class

    def passive(cls, skill_class):
        """Add a skill class to the hero class's :attr:`passive_classes`.

        Designed to be used as a decorator:

        .. code-block:: python

            class MyHero(Hero):
                ...

            @MyHero.passive
            class MySkill(Skill):
                ...

        :param type skill_class:
            Skill to add to the hero's passives
        """
        if skill_class in cls.passive_classes:
            raise ValueError(
                "Passive class {0} already added to a hero.".format(skill_class))
        cls.passive_classes.append(skill_class)
        return skill_class

    def __call__(cls, *args, **kwargs):
        """Instantiate the class and give it instances of its skills.

        Adds an instance of each skill class in the hero class's
        :attr:`skill_classes` list to the hero being instantiated.
        """
        instance = super().__call__(*args, **kwargs)
        for skill_class in cls.skill_classes:
            instance.skills[skill_class.class_id] = skill_class(instance)
        for skill_class in cls.passive_classes:
            instance.passives[skill_class.class_id] = skill_class(instance)
        return instance


class Hero(Entity, metaclass=_HeroMeta):
    """The main entity and idea of the plugin.

    Each hero has its own unique set of skills which give
    the hero/player additional powers and improve his stats.

    These skills can be upgraded to be more powerful with
    :attr:`skill_points`, which are rewarded from leveling up.
    Heroes also have passives which are equal to skills
    but they can not be leveled through :attr:`skill points`
    and they are always active regardless of their level.

    Levels in turn are gained by filling the hero's :attr:`xp_quota`,
    a value which indicates how many experience points the hero needs
    to level up and gain a skill point. These experience points
    (:attr:`xp`) are gained from kills and game objectives.

    The :attr:`xp_quota` will increase as the hero levels up,
    to compensate the extra powers granted by the upgraded skills.
    Upon a hero reaching its maximum level (if any), the quota will
    jump up to infinite (``math.inf``).
    """

    def __init__(self, owner, level=0, xp=0):
        """Initialize the hero entity.

        :param warcraft.player.Player owner:
            The player who owns the hero
        :param int level:
            Initial level of the hero
        :param int xp:
            Initial xp of the hero
        """
        super().__init__(owner, level)
        self._xp = xp
        self.skills = collections.OrderedDict()
        self.passives = collections.OrderedDict()

    @property
    def xp(self):
        return self._xp

    @xp.setter
    def xp(self, value):
        if value < self.xp:
            self.take_xp(self.xp - value)
        if value > self.xp:
            self.give_xp(value - self.xp)

    def take_xp(self, amount):
        """Take experience points from the hero.

        If the hero's :attr:`xp` goes to a negative value, the hero
        will be leveled down and his experience points will be increased
        at the same pace, until :attr:`xp` reaches a positive value.

        :param int amount:
            Amount of xp to take from the hero
        """
        if amount < 0:
            raise ValueError(
                "take_xp() received a negative value, use give_xp() instead.")

        initial_level = self.level
        self._xp -= amount

        while self.level > 0 and self._xp < 0:
            self.level -= 1
            self._xp += self.xp_quota

        level_difference = initial_level - self.level
        if level_difference > 0:
            warcraft.listeners.OnHeroLevelDown.manager.notify(
                hero=self, player=self.owner, levels=level_difference)

    def give_xp(self, amount):
        """Give experience points to the hero.

        If the hero's :attr:`xp` exceeds the hero's :attr:`xp_quota`,
        the hero will be leveled up and his experience points will
        decrease at the same pace, until :attr:`xp_quota` is larger
        than :attr:`xp`'s current value.

        :param int amount:
            Amount of xp to give to the hero
        """
        if amount < 0:
            raise ValueError(
                "give_xp() received a negative value, use take_xp() instead.")

        initial_level = self.level
        self._xp += amount

        while not self.on_max_level() and self._xp >= self.xp_quota:
            self._xp -= self.xp_quota
            self._level += 1

        level_difference = self.level - initial_level
        if level_difference > 0:
            warcraft.listeners.OnHeroLevelUp.manager.notify(
                hero=self, player=self.owner, levels=level_difference)

    @property
    def xp_quota(self):
        if self.on_max_level():
            return math.inf
        return 80 + 15 * self.level

    @property
    def skill_points(self):
        used_points = sum(skill.level for skill in self.skills.values())
        return self.level - used_points

    def can_upgrade_skill(self, skill):
        """Check if a hero can upgrade a skill.

        Makes sure that the hero actually owns the skill, that he has
        enough :attr:`skill_points` to upgrade the skill, and that
        the skill has not reached its maximum level yet.
        """
        return (skill.class_id in self.skills and self.skill_points > 0
                and not skill.on_max_level())

    def upgrade_skill(self, skill):
        """Spend a skill point to upgrade a skill.

        This will raise a :class:`ValueError` if the skill cannot be
        upgraded, so it's recommended to use :meth:`can_upgrade_skill`
        before attempting to upgrade.
        """
        if not self.can_upgrade_skill(skill):
            raise ValueError(
                "Unable to upgrade skill {0}.".format(skill))
        skill.level += 1
        warcraft.listeners.OnSkillUpgrade.manager.notify(
            skill=skill, hero=self, player=self.owner)

    def can_downgrade_skill(self, skill):
        """Check if a hero can downgrade a skill.

        Makes sure that the hero actually owns the skill and that
        the skill is not already on level zero.
        """
        return skill.class_id in self.skills and skill.level > 0

    def downgrade_skill(self, skill):
        """Downgrade a skill to receive a skill point.

        This will raise a :class:`ValueError` if the skill cannot be
        downgraded, so it's recommended to use
        :meth:`can_downgrade_skill` before attempting to downgrade.
        """
        if not self.can_downgrade_skill(skill):
            raise ValueError(
                "Unable to downgrade skill {0}.".format(skill))
        skill.level -= 1
        warcraft.listeners.OnSkillDowngrade.manager.notify(
            skill=skill, hero=self, player=self.owner)

    def reset_skills(self):
        """Reset all of the hero's skills back to level zero."""
        for skill in self.skills.values():
            skill.level = 0
            warcraft.listeners.OnSkillDowngrade.manager.notify(
                skill=skill, hero=self, player=self.owner)

    def execute_skills(self, event_name, event_args):
        """Execute hero's skills for an event.

        Forwards the arguments to the ``execute`` method of the skills
        that have been upgraded to at least level one.
        """
        for skill in self.skills.values():
            if skill.level > 0:
                skill.execute(event_name, event_args)
        for skill in self.passives.values():
            skill.execute(event_name, event_args)
