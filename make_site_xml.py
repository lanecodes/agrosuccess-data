"""
make_site_xml.py
~~~~~~~~~~~~~~~~

Pull together data from various sources to produce a `site_parameters.xml`
file for each study site.
"""
from collections import namedtuple
from pathlib import Path

import pandas as pd

import unidecode

from pyproj import Proj, transform
from osgeo import gdal

import xml.etree.ElementTree as etree
from xml.dom import minidom

GridCellDims = namedtuple('GridCellDims', ['x', 'y'])


def build_all_data_df(output_root_dir: Path) -> pd.DataFrame:
    """Construct a single dataframe containing all site parameter data."""
    site_loc_df = (
        pd.read_csv(output_root_dir / 'site_location_info.csv')
        .assign(sitecode=lambda df: sitename_to_sitecode(df['sitename']))
        .set_index('sitecode')
        .pipe(lambda df: df.join(make_easting_northing_df(df)))
    )

    site_precip_s = (
        pd.read_csv(output_root_dir / 'site_precipitation.csv')
        .set_index('sitecode')
        .mean(1)  # Series containing mean taken across the year for each site
        .rename('monthly_mean_precip')
        .round(decimals=0)
        .astype(int)
    )

    site_annual_precip_and_temp_df = (
        pd.read_csv(output_root_dir / 'tot_precip_mean_temp.csv')
        .assign(sitecode=lambda df: sitename_to_sitecode(df['sitename']))
        .drop(columns='sitename')
        .set_index('sitecode')
        .assign(annual_precip_mm=lambda df: (
            df['annual_precip_mm'].round(decimals=0).astype(int)
        ))
    )

    wind_dir_df = (
        pd.read_csv(output_root_dir / 'site_wind_dir_probs.csv')
        .assign(sitecode=lambda df: sitename_to_sitecode(df['sitename']))
        .drop(columns='sitename')
        .set_index('sitecode')
        .rename(lambda x: 'wind_dir_' + x, axis=1)
        .round(decimals=6)
    )

    wind_speed_df = (
        pd.read_csv(output_root_dir / 'site_wind_speed_class_prob.csv')
        .assign(sitecode=lambda df: sitename_to_sitecode(df['sitename']))
        .drop(columns='sitename')
        .set_index('sitecode')
        .rename(lambda x: 'wind_speed_' + x, axis=1)
        .round(decimals=6)
    )

    site_grid_cell_dims_df = (
        pd.DataFrame.from_dict({
            site_code: read_grid_cell_dimensions(
                output_root_dir / site_code / 'hydrocorrect_dem.tif'
            ) for site_code in site_loc_df.index
        }, orient='index')
        .rename(lambda name: 'cell_size_' + name, axis=1)
        .round(decimals=2)
    )

    select_cols = (
        ['sitename', 'elevation', 'latdd', 'londd', 'easting',
         'northing', 'cell_size_x', 'cell_size_y', 'monthly_mean_precip',
         'annual_precip_mm', 'mean_temp_degc']
        + ['wind_dir_' + x for x in 'N|NE|E|SE|S|SW|W|NW'.split('|')]
        + ['wind_speed_' + x for x in ('low', 'medium', 'high')]
    )

    return (
        site_loc_df
        .join(site_precip_s)
        .join(site_annual_precip_and_temp_df)
        .join(wind_dir_df)
        .join(wind_speed_df)
        .join(site_grid_cell_dims_df)
        .loc[:, select_cols]
    )


def read_grid_cell_dimensions(geotiff_file: Path) -> GridCellDims:
    raster = gdal.Open(str(geotiff_file))
    gt = raster.GetGeoTransform()
    raster = None
    return GridCellDims(x=gt[1], y=-gt[5])


def make_easting_northing_df(site_loc_df: pd.DataFrame) -> pd.DataFrame:
    """Make a new dataframe indexed by sites containing easting /northing.

    Uses the 'latdd' and 'londd' columns from `site_loc_df`.
    """
    return pd.DataFrame(
        site_loc_df
        .apply(lambda s: to_madrid1870(s['latdd'], s['londd']),axis=1)
        .values.tolist(),
        index=site_loc_df.index,
        columns=['easting', 'northing']
    ).round(decimals=2)


def to_madrid1870(lat: float, lon: float):
    """Convert coordinates from WGS84 to Madrid 1870 (EPSG:2062).

    Args:
        lat: WGS84 latitude
        lon: WGS84 longitude

    Returns:
        tuple: (x, y) coordinate pair in Madrid 1870 coordinates
    """
    src = Proj('epsg:4326')
    tgt = Proj('epsg:2062')

    return transform(src, tgt, lon, lat, always_xy=True)


def sitename_to_sitecode(sitename_s: pd.Series) -> pd.Series:
    return (
        sitename_s
        .apply(unidecode.unidecode)
        .str.replace(' ', '_').str.lower()
    )


def write_site_xml(site_s: pd.Series, output_dir_root: Path) -> None:
    """Write site data as an XML file."""
    site_code = site_s.name
    out_file = output_dir_root / site_code / 'site_parameters.xml'
    xml_str = site_data_to_xml(site_s).decode('utf-8')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(minidom.parseString(xml_str).toprettyxml(indent="  "))


def site_data_to_xml(site_s: pd.Series) -> bytes:
    """Encode site data as a pretty printed XML string."""
    site_s = site_s.astype(str)

    root = etree.Element('parameters')
    etree.SubElement(root, 'siteName').text = site_s['sitename']
    etree.SubElement(root, 'siteCode').text = site_s.name

    climate = etree.SubElement(root, 'climate')
    monthly_precip = etree.SubElement(climate, 'meanMonthlyPrecipitation',
                                      units='mm')
    monthly_precip.text = site_s['monthly_mean_precip']
    annual_precip = etree.SubElement(climate, 'meanAnnualPrecipitation',
                                     units='mm')
    annual_precip.text = site_s['annual_precip_mm']
    mean_annual_temp = etree.SubElement(climate, 'meanAnnualTemperature',
                                        units='°C')
    mean_annual_temp.text = site_s['mean_temp_degc']

    wind = etree.SubElement(climate, 'wind')
    wind_direction = etree.SubElement(wind, 'directionProb')
    for direction in 'N|NE|E|SE|S|SW|W|NW'.split('|'):
        col_name = 'wind_dir_' + direction
        etree.SubElement(wind_direction, direction).text = site_s[col_name]
    wind_speed = etree.SubElement(wind, 'speedProb')
    for speed in ['low', 'medium', 'high']:
        col_name = 'wind_speed_' + speed
        etree.SubElement(wind_speed, speed).text = site_s[col_name]

    geographic = etree.SubElement(root, 'geographic')
    elev = etree.SubElement(geographic, 'elevation', units='m')
    elev.text = site_s['elevation']

    coordinates = etree.SubElement(geographic, 'coordinates')
    wgs84 = etree.SubElement(coordinates, 'wgs84')
    etree.SubElement(wgs84, 'latitude').text = site_s['latdd']
    etree.SubElement(wgs84, 'longitude').text = site_s['londd']
    madrid1870 = etree.SubElement(coordinates, 'madrid1870')
    etree.SubElement(madrid1870, 'easting').text = site_s['easting']
    etree.SubElement(madrid1870, 'northing').text = site_s['northing']

    raster = etree.SubElement(geographic, 'raster')
    px_x = etree.SubElement(raster, 'gridCellPixelSizeX', units='m')
    px_x.text = site_s['cell_size_x']
    px_y = etree.SubElement(raster, 'gridCellPixelSizeY', units='m')
    px_y.text = site_s['cell_size_y']

    return etree.tostring(root, encoding='utf-8')


if __name__ == '__main__':
    OUTPUT_ROOT_DIR = Path('outputs')
    master_df = build_all_data_df(OUTPUT_ROOT_DIR)
    test = site_data_to_xml(master_df.loc['navarres'])
    master_df.apply(write_site_xml, output_dir_root=OUTPUT_ROOT_DIR, axis=1)
