# coding utf-8
"""Extract mean annual precipitation values for study sites.

Using the BC paleo-GCM data available from the below URL, extract the
mid-holocene average monthly precipitation values for each study site.

http://www.worldclim.org/paleo-climate1

Write this to the intermediate file ssite_precip_data.pkl to avoid
re-downloading and/ or re-extracting data from required raster cells (this
turned out to be more expensive than anticipated).

Process the resulting dictionary into a pandas.DataFrame, calculate averages
and write to tab-separated summary file ssite_precipitation.tsv

"""
import logging
from pathlib import Path
import os
import pickle
from subprocess import check_output
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import unidecode

import pandas as pd

import requests
from bs4 import BeautifulSoup

def read_site_location_df(output_dir_root: Path):
    """"Retrieve site location dataframe from file."""
    fname = output_dir_root / 'site_location_info.csv'
    try:
        return pd.read_csv(fname).set_index('sitename')
    except FileNotFoundError:
        logging.error(f'Could not find file {fname}.')


def download_file(url: str, output_dir: Path=None) -> Path:
    """"Download a file from URL. Write into `output_dir` if given."""
    base_name = Path(url.split('/')[-1])
    full_name = output_dir / base_name if base_name else base_name
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(full_name, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return full_name


def extract_precip_data_df(site_loc_df: pd.DataFrame,
                           zipf: ZipFile) -> pd.DataFrame:
    """Return dataframe containing Holocene average monthly precipitation.

    Columns are month numbers (1 - 12) and index is study site names.
    """
    site_precip_df = pd.DataFrame()
    with TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        for tif_file in zipf.namelist():
            logging.info('processing: ' + tif_file)
            zipf.extract(tif_file, path=tmpdir)
            for site in site_loc_df.index:
                month_num = _extract_month_from_filename(tif_file)
                lat, lon = site_loc_df.loc[site, ['latdd', 'londd']]
                precip = _extract_monthly_precip_from_file(
                    str(tmpdir / tif_file), lat, lon
                )
                site_precip_df.loc[site, month_num] = precip

            os.remove(tmpdir / tif_file)

    return (
        site_precip_df
        .sort_index(axis=1)
        .pipe(lambda df: df.set_index(df.index.rename('sitecode')))
        .reset_index()
        .assign(sitecode=lambda df: (
            df['sitecode'].apply(unidecode.unidecode)
            .str.replace(' ', '_').str.lower()
        ))
        .set_index('sitecode')
    )


def _extract_month_from_filename(fname):
    """Extract month number from precipitation file name"""
    return  str(fname[7:].split('.tif')[0])


def _extract_monthly_precip_from_file(fname: str, lat: float,
                                      lon: float) -> float:
    """Return Holocene average precipitation for given month and coordinates.

    Each file is average monthly precipitation varying across space.

    This function extracts the annual monthly precipitation for a specific
    location corresponding to the month represented by the file `fname`.
    """
    res = check_output(
         f'gdallocationinfo -xml -wgs84 {fname} {lon} {lat}', shell=True
    )

    return float(BeautifulSoup(res, 'xml').Value.string)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pwd = os.getcwd().split('/')[-1]
    OUTPUT_DIR_ROOT = (Path('../outputs') if pwd == 'precipitation'
                       else Path('outputs'))
    TMP_DIR = Path('../tmp') if pwd == 'precipitation' else Path('tmp')

    PRECIP_DATA_URL = ('http://biogeo.ucdavis.edu/data/climate/cmip5/mid/'
                       'bcmidpr_30s.zip')

    local_zip_fname = TMP_DIR / 'bcmidpr_30s.zip'

    site_loc_df = read_site_location_df(OUTPUT_DIR_ROOT)

    try:
        zipf = ZipFile(local_zip_fname)
    except IOError:
        logging.info('Could not find precipitation zip file, '
                     'downloading from web...')

        local_zip_fname = download_file(PRECIP_DATA_URL, TMP_DIR)
        logging.info('Finished downloading precipitation data')

        zipf = ZipFile(local_zip_fname)

    logging.info('Extracting precipitation data from zipfile')
    site_precip_df = extract_precip_data_df(site_loc_df, zipf)
    zipf.close()

    logging.info('Writing precipitation data to csv...')
    site_precip_df.to_csv(OUTPUT_DIR_ROOT / 'site_precipitation.csv')
    logging.info('Finished processing precipitation data.')
