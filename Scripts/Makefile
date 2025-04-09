.PHONY: archive

test:
	PYTHONPATH=. pytest tests/

run:
	python get_data.py

coverage:
	PYTHONPATH=. pytest --cov=Scripts --cov-report=term-missing --ignore=visualise_data.py

htmlcov:
	PYTHONPATH=. pytest --cov=Scripts --cov-report=html:../htmlcov --ignore=visualise_data.py

timeseries:
	python get_timeseries.py

clean:
	python clean_outputs.py

view: 
	python visualise_data.py --archive "$(archive)" 

archive:
	python archive_data.py \
		$(if $(from), --from-dir="$(from)") \
		$(if $(label), --label="$(label)")