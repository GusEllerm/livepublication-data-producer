test:
	PYTHONPATH=. pytest tests/

run:
	python get_data.py

view:
	python test_geo.py

coverage:
	PYTHONPATH=. pytest --cov=utils --cov-report=term-missing --ignore=test_geo.py

htmlcov:
	PYTHONPATH=. pytest --cov=utils --cov-report=html