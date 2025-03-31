test:
	PYTHONPATH=. pytest tests/

run:
	python get_data.py

view:
	python test_geo.py