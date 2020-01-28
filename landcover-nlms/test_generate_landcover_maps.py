"""
test_generate_landcover_maps.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import logging
from typing import Dict

import pytest

import numpy as np

from generate_landcover_maps import array_int_replace, InitLctProportions

logging.getLogger().setLevel(logging.DEBUG)

def test_lct_proportions_defaults():
    lp = InitLctProportions(pine=0.5, oak=0.3, shrubland=0.2)
    assert lp.oak == pytest.approx(0.3)
    assert lp.pine == pytest.approx(0.5)


def test_lct_proportions_sum_rule():
    with pytest.raises(ValueError):
        InitLctProportions(pine=0.5, oak=0.3)


def test_array_int_replace():
    mapper = {3: 1, 1: 3, 2: 0}

    start_array = np.array([
        [1, 3, 1],
        [2, 2, 2],
        [1, 1, 1],
    ])

    start_array_error = np.array([
        [0, 3, 1],
        [2, 2, 2],
        [1, 1, 1],
    ])

    end_array = np.array([
        [3, 1, 3],
        [0, 0, 0],
        [3, 3, 3],
    ])

    assert np.array_equal(end_array, array_int_replace(start_array, mapper))
    with pytest.raises(ValueError):
        array_int_replace(start_array_error, mapper)
