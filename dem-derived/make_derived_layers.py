"""
make_derived_layers.py
~~~~~~~~~~~~~~~~~~~~~~

Script which takes tif files containing Digital Elevation Models for study
sites and processes them to generate the following for each study site:

1. binary aspect maps
2. slope maps
3. flow direction maps
4. soil type maps

Apart from the digital elevation models, the script takes the file
`site_metadata.csv` as input. This is used to determine which study sites
are being considered.
"""
from pathlib import Path
import logging
import os

import pandas as pd

import demproc

from uniform_soil_type import UniformSoilMapGenerator


def make_derived_maps_for_site(site_name: str, output_root: Path) -> None:
    """Generate derived maps for `site_name`.

    These maps will be put in the directory `<output_root>/<site_name>`.
    """
    initial_dir = os.getcwd()
    try:
        os.chdir(output_root / site_name)
    except FileNotFoundError:
        logging.error('Could not find directory for output. Check output '
                      f'directory for {site_name} exists.')
    try:
        demproc.derive_all('dem.tif', site_name)
    except Exception:
        logging.error(f'Could not generate DEM-derived maps for {site_name}')
    finally:
        os.chdir(initial_dir)

    _rename_derived_maps_for_site(site_name, output_root)
    _make_soil_maps_for_site(site_name, output_root)


def _rename_derived_maps_for_site(site_name: str, output_root: Path) -> None:
    rename_map = {
        site_name + '_binary_aspect.tif': 'binary_aspect.tif',
        site_name + '_flowdir.tif': 'flow_dir.tif',
        site_name + '_slope.tif': 'slope.tif',
        site_name + '_continuous_aspect.tif': 'continuous_aspect.tif',
        site_name + '_hydrocorrect_dem.tif': 'hydrocorrect_dem.tif',
    }
    output_dir = output_root / site_name
    for old, new in rename_map.items():
        try:
            os.rename(output_dir / old, output_dir / new)
        except Exception:
            logging.error(f'Could not rename {output_dir / old}')


def _make_soil_maps_for_site(site_name: str, output_root: Path) -> None:
    """Generate uniform soil maps for named site.

    Uses hydrologically correct DEM for site as a template to ensure resulting
    soil map has the correct dimensions and geographical projection.
    """
    initial_dir = os.getcwd()
    output_dir = output_root / site_name
    os.chdir(output_dir)
    generator = UniformSoilMapGenerator('hydrocorrect_dem.tif')
    for soil_type in list('ABCD'):
        generator.to_geotiff(f'uniform_soil_map_{soil_type}.tif', soil_type)
    os.chdir(initial_dir)


if __name__ == '__main__':
    pwd = os.getcwd().split('/')[-1]
    OUTPUT_DIR_ROOT = (Path('../outputs') if pwd == 'dem-derived'
                       else Path('outputs'))

    print(OUTPUT_DIR_ROOT)

    site_meta_df = pd.read_csv(OUTPUT_DIR_ROOT / 'site_metadata.csv')
    for _, site in site_meta_df.iterrows():
        make_derived_maps_for_site(site['sitecode'], OUTPUT_DIR_ROOT)
