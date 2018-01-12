"""Package for all of the Warcraft's own entities."""

# Warcraft imports
from warcraft.entities.entity import Entity
from warcraft.entities.hero import Hero
from warcraft.entities.skill import Skill
from warcraft.entities.skill import RepeatSkill

__all__ = (
    'Entity',
    'Hero',
    'Skill',
    'RepeatSkill',
)
