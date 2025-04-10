run:
	make -C livepublication_data_producer run

timeseries:
	make -C livepublication_data_producer timeseries

view:
	make -C livepublication_data_producer view

coverage:
	make -C livepublication_data_producer coverage 

htmlcov:
	make -C livepublication_data_producer htmlcov

clean:
	make -C livepublication_data_producer clean

test:
	make -C livepublication_data_producer test

archive:
	make -C livepublication_data_producer archive
