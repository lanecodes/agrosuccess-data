# Generate input data for AgroSuccess model

This project contains all the code needed to generate the input data for the
study sites considered in the AgroSuccess model.

## Setup

Create a virtual environment with required dependencies
```bash
conda env create -f as_data_env.yml
```

Activate the newly created environment

```bash
conda activate as_data
```

## Input data

The following files have proved difficult to automatically generate by script
and should be downloaded manually via a browser and placed in the `inputs`
directory of this project.

- `dumpall_epd_db.sql.gz` contains a Postgres dump of the European Pollen Database
  downloaded from the [EPD website][epd-website-downloads]. Look for 'EPD Postgres'
  and download the version available there.
- `UNdata_Export_20191205_131516780.zip` is a file containing district-level
   wind speed data for Portugal available from the
   [UN data portal][UN-portugal-wind]. Navigate to the linked page, click
   'Download' and select the comma separated csv option.

[epd-website-downloads]: http://europeanpollendatabase.net/data/downloads/
[UN-portugal-wind]: http://data.un.org/Data.aspx?d=CLINO&f=ElementCode%3a16%3bCountryCode%3aPO&c=2,5,6,7,10,15,18,19,20,22,24,26,28,30,32,34,36,38,40,42,44,46&s=CountryName:asc,WmoStationNumber:asc,StatisticCode:asc&v=1

## Generate data for simulations

Ideally it would be possible to simply run `make all` to generate the all
required data (see TODO 1 below). However at present the way to generate all
data is to run the following:

```bash
make pollen
make dem
make nlm
make climate
make wind
make xml
make test
```

## Dependencies

- make
- git
- conda
- docker
- docker-compose
- [gdal](https://gdal.org/)
- [taudem](http://hydrology.usu.edu/taudem/taudem5/index.html)

## TODOs

### 1. Generate all data with `make all`

The process of specifying all targets in the Makefile is complicated by the
fact that all targets apart from `pollen` need to be parameterised by the site
names which are only generated in the `pollen` step. Seek a way to improve this
process.

See [guidance][make-pipeline] on how to use `make` for data pipelines properly.
See also th GNU make documentation on how to write targets with
[multiple outputs][make-multi-targets].

[make-multi-targets]: https://www.gnu.org/software/make/manual/html_node/Multiple-Targets.html
[make-pipeline]: https://byronjsmith.com/make-bml/
