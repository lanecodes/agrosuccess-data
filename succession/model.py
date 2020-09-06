"""
model.py
~~~~~~~~

Data model used to represent ecological succession rules.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Union


@dataclass
class _EnvrProposition:
    """Base class representing an actual or possible environmental state."""
    @classmethod
    def fields(cls):
        """List of fields included in the class.

        This method can be used to avoid mypy errors that occurr when accessing
        ``.__dataclass_fields__`` directly.
        """
        return cls.__dataclass_fields__.keys()


@dataclass
class EnvrAntecedent(_EnvrProposition):
    """Combination of physical conditions leading to ecological transition."""
    start_state: str
    succession_pathway: str
    aspect: str
    pine_seeds: bool
    oak_seeds: bool
    deciduous_seeds: bool
    water: str


@dataclass
class EnvrConsequent(_EnvrProposition):
    """Ecological transition resulting from a specific `EnvrAntecedent`."""
    target_state: str
    transition_time: int


TransitionRule = Tuple[EnvrAntecedent, EnvrConsequent]
SuccessionModel = Dict[str, Union[str, Iterable[TransitionRule]]]


def assemble_succession_model(model_id: str,
                              rules: Iterable[TransitionRule]) -> SuccessionModel:
    return {'model_ID': model_id, 'sucession_rules': rules}
