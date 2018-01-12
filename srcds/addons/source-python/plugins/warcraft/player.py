# Python 3 imports
import collections

# Source.Python imports
from players.entity import Player as SpPlayer

# Warcraft imports
from warcraft.entities import Hero

__all__ = (
    'Player',
)


class Player(SpPlayer):
    """Player class with support for managing Warcraft heroes.

    Each player has an ordered dictionary of his heroes in the format
    of ``{hero.class_id: hero}`` stored into :attr:`heroes` attribute.
    The player also has a :attr:`hero` attribute to store the hero
    he's currently playing with.
    """

    def __init__(self, index):
        """Initialize the player.

        :param int index:
            Index of the player entity
        """
        super().__init__(index)
        self.heroes = collections.OrderedDict()
        self._hero = None

    @property
    def hero(self):
        return self._hero

    @hero.setter
    def hero(self, value):
        if not isinstance(value, Hero):
            raise ValueError(
                "Attempt to set player's hero to a non hero value {0}".format(value))
        if value.class_id not in self.heroes:
            raise ValueError(
                "Hero {0} not owned by player.".format(value))
        self._hero = value

    def calculate_total_level(self):
        """Calculate the total level of all of player's heroes."""
        return sum(hero.level for hero in self.heroes.values())
