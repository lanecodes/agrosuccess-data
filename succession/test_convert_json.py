"""
test_write_json.py
~~~~~~~~~~~~
"""
import pytest

from model import assemble_succession_model, EnvrAntecedent, EnvrConsequent
from convert_json import (
    serialize_succession_model
)


@pytest.fixture
def example_antecedents():
    return [
        EnvrAntecedent(
            start_state='Oak',
            succession_pathway='regeneration',
            aspect='north',
            pine_seeds=True,
            oak_seeds=False,
            deciduous_seeds=True,
            water='hydric'
        ),
        EnvrAntecedent(
            start_state='TransForest',
            succession_pathway='secondary',
            aspect='north',
            pine_seeds=False,
            oak_seeds=False,
            deciduous_seeds=False,
            water='xeric'
        ),
        EnvrAntecedent(
            start_state='Shrubland',
            succession_pathway='secondary',
            aspect='north',
            pine_seeds=False,
            oak_seeds=False,
            deciduous_seeds=True,
            water='hydric'
        ),
    ]


@pytest.fixture
def example_consequents():
    return [
        EnvrConsequent(target_state='TransForest', transition_time=30),
        EnvrConsequent(target_state='Pine', transition_time=20),
        EnvrConsequent(target_state='Deciduous', transition_time=15),
    ]


def test_antecedent_to_json(example_antecedents):
    pass


def test_transition_rule_iterable(example_antecedents, example_consequents):
    trans_rules = zip(example_antecedents, example_consequents)
    model = assemble_succession_model('test_model', trans_rules)
    serialize_succession_model(model)
