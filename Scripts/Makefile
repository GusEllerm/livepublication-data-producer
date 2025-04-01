test:
	PYTHONPATH=. pytest tests/

run:
	python get_data.py

view:
	python visualise_data.py

coverage:
	PYTHONPATH=. pytest --cov=utils --cov-report=term-missing --ignore=visualise_data.py

htmlcov:
	PYTHONPATH=. pytest --cov=utils --cov-report=html:../htmlcov --ignore=visualise_data.py

timeseries:
	python get_timeseries.py

view_timeseries:
	python visualise_timeseries.py

clean:
	python clean_outputs.py