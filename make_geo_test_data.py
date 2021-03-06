"""
make_geo_test_data.py
~~~~~~~~~~~~~~~~~~~~~

Generates GeoTiff files needed to test the AgroSuccess model.
"""
import os
from pathlib import Path
import sys

import numpy as np

from osgeo import gdal

import demproc
from demproc.dummy import make_dummy_hydro_incorrect_dem
from demproc.dummy import create_dummy_geotiff_from_array as gtiff_from_array

OUTPUT_DIR = Path('outputs/test_data')
OUTPUT_DIR.mkdir(exist_ok=True)
os.chdir(OUTPUT_DIR)

# ----------- 3x3 DEMs used to test flow direction network classes ------------
# These classes are likely to be depreciated, but tests maintained in case a
# use is found for them.
gtiff_from_array("hydro_correct_dummy.tif",
    np.array([[1, 1, 3],
              [3, 3, 3],
              [3, 4, 4]]))

gtiff_from_array("hydro_incorrect_dummy.tif",
    np.array([[1, 1, 5],
              [3, 3, 3],
              [3, 4, 4]]))

# ----------------------------- 3x3 Test Grids --------------------------------
# Used to test SiteBoundaryConds and inheriting classes
# DEM derived data
make_dummy_hydro_incorrect_dem("dummy_3x3_hydro_incorrect_dem.tif")
demproc.derive_all("dummy_3x3_hydro_incorrect_dem.tif", "dummy_3x3")

# Write lct map, mix of pine (5) , oak (8) and burnt(1)
gtiff_from_array("dummy_3x3_lct_oak_pine_burnt.tif",
    np.array([[5, 5, 1], [1, 1, 1], [8, 8, 8]]))

# write soil type map, all type A soil
gtiff_from_array("dummy_3x3_soil_type_uniform_A.tif", np.zeros((3, 3)))

# Write succession state map, uniform  soil type map,
gtiff_from_array("dummy_3x3_succession_state_mix.tif",
    np.array([[0, 0, 0,], [0, 1, 1], [1, 1, 1]]))

# ----------------------------- 3x4 Test Grid ---------------------------------
# Used to test error is thrown if a grid within unexpected dimensions is loaded
# into AgroSuccess
gtiff_from_array("dummy_3x4_lct_oak_pine_burnt.tif",
    np.array([[5, 5, 1, 1], [1, 1, 1, 1], [8, 8, 8, 8]]))

# --------------- 51 x 51 Test grids for integration testing ------------------
# Generate larger versions of the 3x3 grids used for unit testing to facilitate
# integration testing. This is done using `np.kron`. See
# https://stackoverflow.com/questions/25676247#answer-25676285
SRC_FILES = [
    "dummy_3x3_binary_aspect.tif",
    "dummy_3x3_continuous_aspect.tif",
    "dummy_3x3_flowdir.tif",
    "dummy_3x3_hydrocorrect_dem.tif",
    "dummy_3x3_hydro_incorrect_dem.tif",
    "dummy_3x3_lct_oak_pine_burnt.tif",
    "dummy_3x3_slope.tif",
    "dummy_3x3_soil_type_uniform_A.tif",
    "dummy_3x3_succession_state_mix.tif",
    "dummy_3x4_lct_oak_pine_burnt.tif",
]

def geotiff_to_array(fname):
    """Read a GeoTiff file, return a numpy array containing grid values."""
    ds = gdal.Open(fname)

    # Get a numpy array representing the source dataset
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()

    return arr

# (50 + (3 - 50%3))//3 = 17, 17*3 = 51. To get a square grid with edge ~ 50
# We should multiply grid with edge 3 by 17...
mult_fac = 17
for fname in SRC_FILES:
    arr = geotiff_to_array(fname)
    new_arr = np.kron(arr, np.ones((mult_fac, mult_fac), dtype=arr.dtype))
    new_name = fname.replace("3x3", "51x51")
    gtiff_from_array(new_name, new_arr)
