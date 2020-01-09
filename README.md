# Generate input data for AgroSuccess model

## Setup

Create a virtual environment with required dependencies
```bash
conda env create -f as_data_env.yml
```

Activate the newly created environment

```bash
conda activate as_data
```

Run `make` to generate data

```bash
make all
```

## Input data

The following files should be placed in the `inputs` folder

- `dumpall_epd_db.sql.gz` contains a Postgres dump of the European Pollen Database
  downloaded from the EPD website
- `epd_extract_config.yml` is a configuration file specifying which study sites
  should be extracted from the EPD.

## Dependencies

- make
- git
- conda
- docker
- docker-compose
- [gdal](https://gdal.org/)
- [taudem](http://hydrology.usu.edu/taudem/taudem5/index.html)
