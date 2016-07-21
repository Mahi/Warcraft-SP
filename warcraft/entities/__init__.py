"""Package for all of the Warcraft's own entities."""

# Warcraft imports
from warcraft.entities.entity import Entity
from warcraft.entities.hero import Hero
from warcraft.entities.skill import callback
from warcraft.entities.skill import Skill

__all__ = (
    'callback',
    'Entity',
    'Hero',
    'Skill',
)
