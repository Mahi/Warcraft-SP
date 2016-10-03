"""Contains the :class:`Skill` base class for all of the skills."""

# Warcraft imports
from warcraft.entities.entity import Entity
from warcraft.utilities import CooldownDict

__all__ = (
    'Skill',
)


class _SkillMeta(type):
    """Metaclass for managing skills' callbacks.

    Adds an :attr:`_event_callbacks` dictionary for each skill class
    and checks to see if any of the skill's methods have been decorated
    with the :func:`callback` function.

    The decorated functions are added to the ``_event_callbacks`` dict
    so that the method is the value and the event's name is the key.

    For example:

    .. code-block:: python

        class MySkill(Skill):

            @callback('player_spawn', 'player_attack')
            def my_callback(self, **event_args):
                ...

            @callback('player_jump')
            def another_callback(self, **event_args):
                ...

    Will result into the following ``_event_callbacks`` dictionary:

    .. code-block:: none

        MySkill._event_callbacks = {
            'player_attack': my_callback,
            'player_jump': another_callback,
            'player_spawn': my_callback,
        }
    """

    def __init__(cls, name, bases, attrs):
        """Initialize the skill class and register its callbacks."""
        super().__init__(name, bases, attrs)
        cls._event_callbacks = {}
        for attr in attrs.values():
            if not hasattr(attr, '_events'):
                continue
            for event_name in attr._events:
                cls._event_callbacks[event_name] = attr


class Skill(Entity, metaclass=_SkillMeta):
    """Base class for skills which grant special powers to heroes.

    These skills are leveled up by the owning
    :class:`warcraft.entities.hero.Hero` instance by spending his
    skill points. In general it's a good idea to have the skill's power
    or cooldown (if any) linked to the skill's :attr:`level` so that
    leveling the skill up actually has a meaning.

    When creating a new skill, register any of its event callbacks
    using the :func:`callback` function:

    .. code-block:: python

        class Bonus_Health(Skill):
            "Gain bonus health upon spawning."
            max_level = 8

            # This will register the callback for 'player_spawn' event
            @callback('player_spawn')
            def _boost_health(self, player, **eargs):
                player.health += self.level * 5

    These registered callbacks will then be executed by
    the :meth:`execute` method automatically upon an event happening.

    Skills can also be given cooldowns through the :attr:`cooldowns`
    dictionary:

    .. code-block:: python

        @callback('player_attack')
        def _add_skull(self, **eargs):
            if self.cooldowns['attack'] <= 0:
                self.skulls += 1
                self.cooldowns['attack'] = 8

        @callback('player_ultimate')
        def _spend_skulls(self, player, **eargs):
            cd = self.cooldowns['ultimate']
            if cd <= 0:
                self.speed += self.skulls * 0.01 * self.level
                self.health += self.skulls + self.level
                self.cooldowns['ultimate'] = 40 - self.skulls
                self.skulls = 0
            else:
                SayText2('Cooldown {cd}').send(player.index, cd=int(cd))
    """

    def __init__(self, owner, level=0):
        """Initialize the skill. Adds the :attr:`cooldowns` attribute.

        :param object owner:
            The owner of the skill
        :param int level:
            Initial level of the skill
        """
        super().__init__(owner, level)
        self.cooldowns = CooldownDict()

    @staticmethod
    def ecallback(*event_names):
        """Register a callback for events based on their names.

        Adds an ``_events`` attribute for the callback which will later
        be used by :class:`_SkillMeta` to parse all of the callbacks.

        :param tuple \*event_names:
            Names of the events to register the callback for
        """
        def decorator(f):
            f._events = event_names
            return f
        return decorator

    def execute(self, event_name, event_args):
        """Execute any registerd callbacks for the event.

        :param str event_name:
            Name of the event which the callbacks should be registerd to
        :param dict event_args:
            Event arguments forwarded to the callbacks
        """
        if event_name in self._event_callbacks:
            self._event_callbacks[event_name](self, **event_args)
