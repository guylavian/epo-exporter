.PHONY: lint test docker-build docker-run fmt install clean

lint:
	python -m pyflakes epo_exporter || true

fmt:
	python -m black epo_exporter || true

test:
	python -m pytest -q || true

install:
	pip install -r requirements.txt
	pip install -e .

docker-build:
	docker build -t epo-exporter:dev .

docker-run:
	docker run --rm -p 9898:9898 \
	  -e EPO_HOST=$$EPO_HOST -e EPO_USERNAME=$$EPO_USERNAME -e EPO_PASSWORD=$$EPO_PASSWORD \
	  epo-exporter:dev

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
