# -*- coding: utf-8 -*-
"""Create a zip cache including a geotiff and landcover proportion summary."""
from dataclasses import dataclass
import csv
from pathlib import Path
import logging
import os
import tempfile
from typing import Dict, List
import zipfile

import numpy as np
import pandas as pd

from init_land_cover_types import LandscapeCoverage, RandomLandcoverGenerator
from constants import AgroSuccessLct

# Age BP at which humans first populated study sites
SSITE_T0 =  pd.Series({'navarres': 7000,
                       'charco_da_candieira': 6500,
                       'atxuri': 5000,
                       'monte_areo_mire': 7300,
                       'algendar': 5000,
                       'san_rafael': 5000}).rename('t0')

SSITE_TREELINES = {
    'navarres': 400,
    # c_da_c can't have treeline at 400 m as elevation all above 600 m
    'charco_da_candieira': 1700,
    # Lower treeline would require ngative shrubland at lower elevation
    'atxuri': 600,
    # All elevation lower than 400 m, no treeline
    'monte_areo_mire': None,
    'algendar': None,
    'san_rafael': 400,
}

# Number of landscapes to generate for each study site
N_LANDSCAPES = 100


@dataclass
class InitLctProportions:
    """Proportions of landscape occupied by land cover types.

    The available fields here reflect the assumption that only deciduous, oak,
    pine and shrubland land cover types are available at the beginning of
    a simulation.
    """
    deciduous: float = 0
    oak: float = 0
    pine: float = 0
    shrubland: float = 0
    grassland: float = 0

    def __post_init__(self):
        total = sum([x for _, x in self.__dict__.items()])
        if abs(total - 1) > 0.0001:
            raise ValueError('Total land cover proportions should sum to 1, '
                             f'not {total}.')


def get_init_lct_props(output_dir_root: Path,
                       ssite_t0: pd.Series) -> Dict[str, InitLctProportions]:
    """Dictionary of land cover type proportions at time of human settlement.

    Keys are site names, values are `InitLctProportions` objects.

    Assumes the existance of the files `<site_name>/lct_pct_ts.csv` within the
    `output_dir_root` directory. Extracts

    Parameters
    ----------
    output_dir_root:
        Path to the agrosuccess-data output directory.
    ssite_t0:
        Series whose index is study site names, and values are first date at
        which people started practicing agriculture at the site.
    """
    site_meta_df = get_site_metadata(output_dir_root)
    t0_props = (
        pd.concat([
            pd.read_csv(output_dir_root / site / 'lct_pct_ts.csv')
            .assign(sitecode=site)
            for site in site_meta_df.index
        ])
        .set_index(['sitecode', 'agebp'])
        .sort_index()
        .filter(regex='^pct_*')  # Drop columns corresponding to derivatives
        .rename(mapper=lambda s: s.replace('pct_', ''), axis='columns')
        .rename(mapper=lambda s: s.replace('_forest', ''), axis='columns')
        .loc[zip(ssite_t0.index, ssite_t0)]  # Extract time slices at t0
        .divide(100)  # Convert percentage to proportion
        .reset_index(level='agebp', drop=True)
    )

    return {site_name: InitLctProportions(**props)
            for site_name, props in t0_props.iterrows()}


def get_site_metadata(output_dir_root: Path) -> pd.DataFrame:
    return (
        pd.read_csv(output_dir_root / 'site_metadata.csv')
        .set_index('sitecode')
    )


def create_landscape_matching_proportions(
        landscape_generator: RandomLandcoverGenerator,
        target_props: InitLctProportions,
        tree_line: int=None,
        upland_props: InitLctProportions=None
    ) -> LandscapeCoverage:
    """Create a landscape with given target proportions.

    If a `tree_line` is optionally specified, we can also specify the
    proportion of the landscape covered with each land cover type in the
    uplands using the `upland_props` parameter. The lowland land cover
    proportions will then be determined so as to produce overall proportions
    matching `target_props`.
    """
    if (tree_line is None) ^ (upland_props is None):
        raise ValueError('If tree_line is given, upland_props must be set.')

    ordered_lct_names = ('deciduous', 'oak', 'pine', 'shrubland', 'grassland')

    landscape = landscape_generator.match_proportions(
        lct_props=[getattr(target_props, x) for x in ordered_lct_names],
        iterations=30,
        upland_props=([getattr(upland_props, x) for x in ordered_lct_names]
                      if upland_props else None),
        tree_line=tree_line if tree_line else None,
    )

    return _remap_landscape_codes(landscape, ordered_lct_names)


def _remap_landscape_codes(landscape: LandscapeCoverage,
                           lct_names: tuple) -> LandscapeCoverage:
    """Change lct codes in landscape to match those in `AgroSuccessLct`.

    Parameters
    ----------
    landscape:
        Landscape for which land cover type codes will be re-mapped.
    lct_names:
        Tuple containing names of land cover types such that `lct_names[n]` is
        the name of the land cover type for which an `n` in cell `(i, j)` of
        the landscape's `landcover_array` attribute indicates that land cover
        of type `lct_names[n]` occupies that cell.
    """
    code_mapper = {i: AgroSuccessLct.from_alias(name.title()).value
                   for i, name in enumerate(lct_names)}

    landscape.landcover_array = array_int_replace(landscape.landcover_array,
                                                  code_mapper)

    return landscape


def array_int_replace(a: np.array, replace: Dict[int, int]) -> np.array:
    """Replace values in `a` using mapping in `replace`.

    Follows `guidance on SO`_.

    .. _guidance on SO: https://stackoverflow.com/questions/46868855
    """
    indexer = np.array([replace.get(i, -1)
                        for i in range(a.min(), a.max() + 1)])
    if indexer[indexer < 0].size > 0:
        raise ValueError('replace dict must contain mappings for all values '
                         'in a.')

    return indexer[(a - a.min())]


def score_landscape(landscape: LandscapeCoverage,
                    total_props: InitLctProportions) -> pd.DataFrame:
    """Calculate a score for each target proportion in the landscape.

    Scores close to 1 indicate the landscape closely approximates the target
    land cover proportions.
    """
    return (
        pd.DataFrame(
            [(x.value, x.alias.lower(), getattr(total_props, x.alias.lower()),
              landscape.landscape_proportions('all')(x.value))
              for x in AgroSuccessLct
              if x.alias.lower() in total_props.__dict__.keys()],
            columns=['lct_code', 'lct_name', 'target_prop', 'landscape_prop']
        )
        .assign(score=lambda df: (
            1 - (df['target_prop'] - df['landscape_prop']).abs()
        ))
        .set_index(['lct_name'])
    )


def make_landscape_cache(output_dir: Path, num_landscapes: int,
                         landscape_generator: RandomLandcoverGenerator,
                         target_props: InitLctProportions,
                         tree_line: int=None,
                         upland_props: InitLctProportions=None) -> None:
    """Create zip of landscapes called init_lct_maps.zip in `output_dir`."""
    with tempfile.TemporaryDirectory() as tmpdir_name:
        tmpdir = Path(tmpdir_name) / 'landcover_cache'
        tmpdir.mkdir()
        for landscape_num in range(num_landscapes):
            logging.info(f'Making file {landscape_num + 1} of {num_landscapes}')
            out_file_base = str(tmpdir / f'init-landcover{landscape_num}')
            landscape = create_landscape_matching_proportions(
                landscape_generator,
                target_props,
                tree_line,
                upland_props
            )
            landscape.to_geotiff(out_file_base + '.tif')
            score = score_landscape(landscape, target_props)
            score.to_csv(out_file_base + '.csv')

        with zipfile.ZipFile(output_dir / 'init_lct_maps.zip', 'w') as z:
            for filename in sorted(os.listdir(tmpdir)):
                file_path = tmpdir / filename
                z.write(file_path, file_path.name)
                os.remove(file_path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    pwd = os.getcwd().split('/')[-1]
    OUTPUT_DIR_ROOT = (Path('../outputs') if pwd == 'landcover-nlms'
                       else Path('outputs'))

    t0_lct_props = get_init_lct_props(OUTPUT_DIR_ROOT, SSITE_T0)

    for site_code, lct_props in t0_lct_props.items():
        logging.info(f'Generating landscapes for {site_code}')
        site_output_dir = OUTPUT_DIR_ROOT / site_code
        generator = RandomLandcoverGenerator(
            str(site_output_dir / 'hydrocorrect_dem.tif')
        )
        tree_line = SSITE_TREELINES[site_code]
        make_landscape_cache(site_output_dir,N_LANDSCAPES, generator,
                             lct_props, tree_line=tree_line,
                             upland_props=(InitLctProportions(shrubland=0.5, grassland=0.5)
                                           if tree_line else None))

        # generator = LandcoverCacheGenerator(
        #     dem_filename=site_output_dir / 'hydrocorrect_dem.tif',
        #     total_props=[
        #         lct_props['deciduous_forest'],
        #         lct_props['oak_forest'],
        #         lct_props['pine_forest'],
        #         lct_props['shrubland'],
        #     ],
        #      # upland all shrubland
        #     upland_props=[0, 0, 0, 1] if SSITE_TREELINES[site_code] else None,
        #     tree_line=SSITE_TREELINES[site_code]
        # )
        # generator.make_cache(site_output_dir / 'init_lct_maps.zip', N_LANDSCAPES)
