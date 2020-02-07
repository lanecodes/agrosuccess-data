"""
total_precip_and_temp.py
~~~~~~~~~~~~~~~~~~~~~~~~

`Download`_ and extract total annual precipitation and average temperature
values produced by the BCC-CSM1-1 GCM. Refer to the '`bioclimatic`_' variables
from `WorldClim`_. See `USGS report`_ for more detailed descriptions of these
variables.

The `BioClim`_ variables relevant for this script are:
    - BIO1: Annual Mean Temperature
    - BIO12: Annual precipitation

I assume that:
    1. The units for BIO1 are °C * 10
    2. The units for BIO12 are millimeters

This is consistent with the units given on the WorldClim website for monthly
average minimum temperature and monthly total precipitation variables.


Note that the precipitation variables extracted in this script differ from
the `extract_mean_precipitation.py` script which looks at average monthly
precipitation.

.. _`Download`: http://biogeo.ucdavis.edu/data/climate/cmip5/mid/bcmidbi_30s.zip
.. _`WorldClim`: http://www.worldclim.org/paleo-climate1
.. _`USGS report`: https://pubs.usgs.gov/ds/691/ds691.pdf
.. _`bioclimatic`: http://worldclim.org/bioclim
"""
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pandas as pd

from extract_mean_precipitation import (
    extract_value_for_point_from_file, download_file, read_site_location_df
)


def extract_value_data_df(site_loc_df: pd.DataFrame, zipf: ZipFile,
                          tif_file: str) -> pd.Series:
    """Return DataFrame containing data from `tif_file` for site locations.

    Index is study site names.
    """
    site_value_s = pd.Series()

    with TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        zipf.extract(tif_file, path=tmpdir)
        for site in site_loc_df.index:
            lat, lon = site_loc_df.loc[site, ['latdd', 'londd']]
            value = extract_value_for_point_from_file(
                str(tmpdir / tif_file), lat, lon
            )
            site_value_s.loc[site] = value

        os.remove(tmpdir / tif_file)

    return site_value_s


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pwd = os.getcwd().split('/')[-1]
    OUTPUT_DIR_ROOT = (Path('../outputs') if pwd == 'climate'
                       else Path('outputs'))
    TMP_DIR = Path('../tmp') if pwd == 'climate' else Path('tmp')

    BIOCLIM_DATA_URL = ('http://biogeo.ucdavis.edu/data/climate/cmip5/mid/'
                        'bcmidbi_30s.zip')

    local_zip_fname = TMP_DIR / 'bcmidbi_30s.zip'

    site_loc_df = read_site_location_df(OUTPUT_DIR_ROOT)

    try:
        zipf = ZipFile(local_zip_fname)
    except IOError:
        logging.info('Could not find bioclimatic zip file, '
                     'downloading from web...')

        local_zip_fname = download_file(BIOCLIM_DATA_URL, TMP_DIR)
        logging.info('Finished downloading bioclimatic data')

        zipf = ZipFile(local_zip_fname)

    precip_s = (
        extract_value_data_df(site_loc_df, zipf, 'bcmidbi12.tif')
        .rename('annual_precip_mm')
    )

    temp_s = (
        extract_value_data_df(site_loc_df, zipf, 'bcmidbi1.tif')
        .div(10)  # TODO Check units in GeoTiff are °C * 10
        .rename('mean_temp_degc')
    )

    precip_temp_df = pd.concat([precip_s, temp_s], axis=1)
    precip_temp_df.index.name = 'sitename'

    data_desc = 'total annual precipitation and mean temperature data'
    logging.info(f'Writing {data_desc} to csv...')
    precip_temp_df.to_csv(OUTPUT_DIR_ROOT / 'tot_precip_mean_temp.csv')
    logging.info(f'Finished processing {data_desc}.')
