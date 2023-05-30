import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from osgeo import gdal

def process_landsat_zip(zipfile_name: Path, reference_tif_file: Path, output_file: Path) -> None:
    abs_ref_file = reference_tif_file.resolve()
    abs_zipfile = zipfile_name.resolve()
    abs_output_file = output_file.resolve()
    try:
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            extracted_tif = _extract_landsatlook_tif(str(abs_zipfile))
            cropped_tif = _match_tif_extents(str(abs_ref_file), extracted_tif, str(abs_output_file))
    finally:
        os.chdir(cwd)
        

def process_landsat_coll2_tiff(tiff_file_name: Path, reference_tif_file: Path, output_file: Path) -> None:
    abs_ref_file = reference_tif_file.resolve()
    abs_tiff_file = tiff_file_name.resolve()
    abs_output_file = output_file.resolve()
    try:
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            cropped_tif = _match_tif_extents(str(abs_ref_file), str(abs_tiff_file), str(abs_output_file))
    finally:
        os.chdir(cwd)


def _extract_landsatlook_tif(zipfile_name, output_dir=None, output_name=None):
    """Extract a georeferenced LandsatLook tif from Earth Explorer zip file.
    
    Given a 'LandsatLook Images with Geographic Reference' zip file downloaded 
    from USGS Earth Explorer https://earthexplorer.usgs.gov, select the 
    Natural Colour .tif file and extract it to the specified output_dir, 
    naming it if given. Essentially this amounts to finding the file in the 
    zip archive which doesnt have a suffix indicating it's a 'Quality' image
    (suffix _QB) or a 'Thermal' image (suffix _TIR).
    
    Args:
        zipfile_name (str): Zipfile to be processed.
        output_dir (Optional[str]): Path to directory in which to save 
            resulting tif file.
        output_name (Optional[str]): Name to give output file.        
    
    Returns:
        str: Path to the output file.
    """
    
    with zipfile.ZipFile(zipfile_name, 'r') as z:
        all_files = z.namelist()
        natural_colour_files = [f for f in all_files 
                                if not(re.match(r'.*_QB.tif|.*_TIR.tif', f))]
        if len(natural_colour_files) < 1:
            raise ValueError('No Natural Colour .tif found in .zip')
        elif len(natural_colour_files) > 1:
            raise ValueError('{0} Natural Colour .tif files found in .zip '\
                             'when only one expected. Check file.')
        else:
            # Only if exactly one natural colour file identified, extract it
            nc_file = natural_colour_files[0]
            z.extract(nc_file, path=output_dir)
            if (output_name and output_dir):
                created_file = os.path.join(output_dir, output_name)
                os.rename(os.path.join(output_dir, nc_file), created_file)
            elif output_dir:
                created_file = os.path.join(output_dir, nc_file)
            elif output_name:
                created_file = output_name
                os.rename(nc_file, created_file)
            else:
                created_file = nc_file
            
            return created_file


def _match_tif_extents(tif_to_match, tif_to_cut, output_name):
    """Use one tif file to crop another to the same extent and projection.
    
    Args:
        tif_to_match (str): Name of a tif file to use as an example whose
            extent and crs we want the other file to match.
        tif_to_cut (str): Name of a tif file to crop and reproject to match
            tif_to_match.
        output_name (str): Name of resulting cropped and reprojected 
            tif file.
            
    Returns:
        str: Path to the output file.   
    """
    src_data = gdal.Open(tif_to_match, gdal.GA_ReadOnly)
    wkt = src_data.GetProjection()
    geoTransform = src_data.GetGeoTransform()
    minx = geoTransform[0]
    maxy = geoTransform[3]
    maxx = minx + geoTransform[1] * src_data.RasterXSize
    miny = maxy + geoTransform[5] * src_data.RasterYSize
    src_data = None
    
    with open('tmp.prj', 'w') as prj:
        # write a temporary well known text file to be used by gdalwarp
        prj.write(wkt)
       
    # specify parameters to be passed to gdalwarp in an external process:
    param = ['gdalwarp', tif_to_cut, output_name, '-overwrite',
             '-t_srs', 'tmp.prj',
             '-te', str(minx), str(miny), str(maxx), str(maxy)]
    
    cmd = ' '.join(param)
    process = subprocess.check_call(cmd, shell=True)
    
    os.remove('tmp.prj')
    
    return output_name