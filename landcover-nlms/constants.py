"""
constants.py
~~~~~~~~~~~~

Constants to be shared across multiple scripts.

Note
----
`AgroSuccessLct` was copied from the `scripts/constants.py` module in the
`agrosuccess-graph` project. It would help make things cleaner to put shared
code like this in a library which can be conda installed and easily shared.
"""
from enum import Enum, unique

@unique
class AgroSuccessLct(Enum):
    """Land cover types and corresponding codes used in AgroSuccess."""
    WATER_QUARRY = (0, "WaterQuarry")
    BURNT = (1, "Burnt")
    BARLEY = (2, "Barley")
    WHEAT = (3, "Wheat")
    DAL = (4, "DAL")
    SHRUBLAND = (5, "Shrubland")
    PINE = (6, "Pine")
    TRANS_FOREST = (7, "TransForest")
    DECIDUOUS = (8, "Deciduous")
    OAK = (9, "Oak")

    def __init__(self, code, alias):
        self._code = code
        self.alias = alias

    @property
    def value(self):
        return self._code

    @classmethod
    def _from_attr(cls, attr, value):
        matching_members = [member for name, member in cls.__members__.items()
                            if getattr(member, attr) == value]
        if not matching_members:
            raise ValueError("No member in {0} with value: {1}"\
                .format(cls, value))
        elif len(matching_members) > 1:
            raise ValueError("Multiple members in {0} with value: {1}"\
                .format(cls, value))
        else:
            return matching_members[0]

    @classmethod
    def from_alias(cls, value):
        return cls._from_attr("alias", value)