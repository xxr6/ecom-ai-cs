.PHONY: install test cov eval try clean

install:
	pip install -r requirements.txt

test:
	pytest -q

cov:
	pytest --cov=ecom_cs --cov-report=term-missing

eval:
	python scripts/run_eval.py

try:
	python chat.py "我的快递到哪了 2024110001"

clean:
	rm -rf .pytest_cache .coverage htmlcov
	find . -name "__pycache__" -type d -exec rm -rf {} +
