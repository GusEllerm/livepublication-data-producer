.PHONY: archive

test:
	PYTHONPATH=. pytest tests/

run:
	python get_data.py

coverage:
	PYTHONPATH=. pytest --cov=utils --cov-report=term-missing tests/

htmlcov:
	PYTHONPATH=. pytest --cov=utils --cov-report=html:../htmlcov tests/

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