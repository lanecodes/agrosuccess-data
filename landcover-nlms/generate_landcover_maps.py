# -*- coding: utf-8 -*-
"""Create a zip cache including a geotiff and landcover proportion summary."""
import csv
from pathlib import Path
import logging
import os
from typing import List
import zipfile

import pandas as pd

from init_land_cover_types import RandomLandcoverGenerator

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
    'charco_da_candieira': 1600,
    # Lower treeline would require negative shrubland at lower elevation
    'atxuri': 600,
    # All elevation lower than 400 m, no treeline
    'monte_areo_mire': None,
    'algendar': None,
    'san_rafael': 400,
}

# Number of landscapes to generate for each study site
N_LANDSCAPES = 5


class LandcoverCacheGenerator(object):
    def __init__(self, dem_filename, total_props, upland_props=None,
                 tree_line=None):

        self.generator = RandomLandcoverGenerator(dem_filename)
        self.total_props = total_props
        self.upland_props = upland_props
        self.tree_line = tree_line
        self.generated_file_list_buffer = []

    def get_scores(self, landscape, total_props):
        scores = []
        for i, prop in enumerate(total_props):
            scores.append([i, prop, landscape.landscape_proportions('all')(i)])
        return scores

    def write_score_csv(self, csv_filename, landscape, total_props):
        with open(csv_filename, "w") as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'target_prop', 'landscape_prop'])
            writer.writerows(self.get_scores(landscape, total_props))

    def generate_landscape_files(self, landscape_num):
        landscape = self.generator.match_proportions(self.total_props, 30,
                                                     self.upland_props,
                                                     self.tree_line)
        landscape_file = 'init-landcover' + str(landscape_num) + '.tif'
        score_csv_file = 'init-landcover' + str(landscape_num) + '.csv'
        landscape.to_geotiff(landscape_file)
        self.write_score_csv(score_csv_file, landscape, self.total_props)
        self.generated_file_list_buffer.append(landscape_file)
        self.generated_file_list_buffer.append(score_csv_file)

    def make_cache(self, cache_name, num_landscapes):
        with zipfile.ZipFile(cache_name, 'w') as z:
            for i in range(num_landscapes):
                logging.info(f'making file {i + 1} of {num_landscapes}')
                self.generate_landscape_files(i)
                for f in self.generated_file_list_buffer:
                    z.write(f)
                    os.remove(f)
                self.generated_file_list_buffer = []


def get_init_lct_props(output_dir_root: Path) -> pd.DataFrame:
    """Get DF of land cover type proportions at time of human settlement.

    Returned dataframe has columns in order:

    0: deciduous_forest
    1: oak_forest
    2: pine_forest
    3: shrubland
    """
    site_meta_df = get_site_metadata(output_dir_root)
    ts = (
        pd.concat([
            pd.read_csv(output_dir_root / site / 'lct_pct_ts.csv')
            .assign(sitecode=site)
            for site in site_meta_df.index
        ])
        .set_index(['sitecode', 'agebp'])
        .sort_index()
        .filter(regex='^pct_*')  # Drop columns corresponding to derivatives
        .rename(mapper=lambda s: s.replace('pct_', ''), axis='columns')
        .divide(100)  # Convert percentage to proportion
    )
    return ts.loc[zip(SSITE_T0.index, SSITE_T0)]


def get_site_metadata(output_dir_root: Path) -> pd.DataFrame:
    return (
        pd.read_csv(output_dir_root / 'site_metadata.csv')
        .set_index('sitecode')
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    pwd = os.getcwd().split('/')[-1]
    OUTPUT_DIR_ROOT = (Path('../outputs') if pwd == 'dem-derived'
                       else Path('outputs'))

    t0_lct_props = get_init_lct_props(OUTPUT_DIR_ROOT)

    for (site_code, _), lct_props in t0_lct_props.iterrows():
        logging.info(f'Generating landscapes for {site_code}')
        site_output_dir = OUTPUT_DIR_ROOT / site_code
        generator = LandcoverCacheGenerator(
            dem_filename=site_output_dir / 'hydrocorrect_dem.tif',
            total_props=[
                lct_props['deciduous_forest'],
                lct_props['oak_forest'],
                lct_props['pine_forest'],
                lct_props['shrubland'],
            ],
             # upland all shrubland
            upland_props=[0, 0, 0, 1] if SSITE_TREELINES[site_code] else None,
            tree_line=SSITE_TREELINES[site_code]
        )
        generator.make_cache(site_output_dir / 'init_lct_maps.zip', N_LANDSCAPES)
