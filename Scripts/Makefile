.PHONY: archive

test:
	PYTHONPATH=. pytest tests/

run:
	python get_data.py

coverage:
	PYTHONPATH=. pytest --cov=utils --cov-report=term-missing --ignore=visualise_data.py

htmlcov:
	PYTHONPATH=. pytest --cov=utils --cov-report=html:../htmlcov --ignore=visualise_data.py

timeseries:
	python get_timeseries.py

clean:
	python clean_outputs.py

archive:
	python archive_data.py \
		$(if $(from), --from-dir="$(from)") \
		$(if $(label), --label="$(label)")