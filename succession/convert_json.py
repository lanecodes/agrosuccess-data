"""
json.py
~~~~~~~

Write set of ecological succession rules to json file.


"""
import collections
import json

from model import SuccessionModel, EnvrAntecedent, EnvrConsequent


def serialize_succession_model(model: SuccessionModel) -> str:
    return json.dumps(model, default=encode_succession_model_component,
                      indent=2)


def encode_succession_model_component(component):
    """Converts complex objects in model into serializable equivalents."""
    if isinstance(component, collections.abc.Iterable):
        return list(component)
    if isinstance(component, EnvrAntecedent):
        d = component.__dict__
        d['__EnvrAntecedent__'] = True
        return d
    if isinstance(component, EnvrConsequent):
        d = component.__dict__
        d['__EnvrConsequent__'] = True
        return d
    else:
        type_name = component.__class__.__name__
        raise TypeError(f"Object of type '{type_name}' is not JSON serializable")
