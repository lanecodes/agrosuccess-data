# Activate the as_data environment in your shell first before calling:
# $ make all
pollen:
	echo "Extracting pollen data..."
	[ -d tmp ] || mkdir tmp
	git clone https://github.com/lanecodes/epd-query.git tmp/epd-query
	cp inputs/dumpall_epd_db.sql.gz tmp/epd-query/data/
	cp inputs/epd_extract_config.yml tmp/epd-query/config/config.yml
	cd tmp/epd-query; docker-compose up --abort-on-container-exit
	sudo chown -R andrew:andrew tmp/epd-query/outputs/
	[ -d outputs ] || mkdir outputs
	mv tmp/epd-query/outputs/site_location_info.csv outputs/
	mv tmp/epd-query/outputs/site_pollen_abundance_ts.csv tmp/
	cd tmp/epd-query; docker-compose down -v
	sudo rm -rf tmp/epd-query
	jupyter nbconvert --to python pollen-abundance/make_lct_timeseries.ipynb
	ipython pollen-abundance/make_lct_timeseries.py
	rm pollen-abundance/make_lct_timeseries.py

dem:
	echo "Downloading DEM data and generating derived maps..."
	jupyter nbconvert --to python dem-derived/download_site_elevation_data.ipynb
	ipython dem-derived/download_site_elevation_data.py
	python dem-derived/make_derived_layers.py
	rm dem-derived/download_site_elevation_data.py

nlm:
	echo "Generating nautral land scape models for initial conditions..."
	python landcover-nlms/generate_landcover_maps.py

precipitation:
	python precipitation/extract_mean_precipitation.py
	echo "precipitation not implemented"

wind:
# TODO check where data output t0
	jupyter nbconvert --to python wind/get_ssite_wind_data.ipynb
	ipython wind/get_ssite_wind_data.py
	rm wimd/get_ssite_wind_data.py

clean:
	rm -f dem-derived/download_site_elevation_data.py
	rm -f wind/get_ssite_wind_data.py
	rm -f pollen-abundance/make_lct_timeseries.py
	rm -f dem-derived/download_site_elevation_data.py
	sudo rm -rf tmp/epd-query
	rm -f tmp/*