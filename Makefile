VERSION ?= "1.0.0"

build:
	docker build -t k8s_user:${VERSION} . 


test: build
	docker run \
		-v `pwd`:/srv/ \
		-it k8s_user:${VERSION} \
		bash -c \
		"pytest -vv --cov-config=.coveragerc --cov=k8s_user tests/ \
			&& coverage html -d reports/"


shell: build
	docker run \
		-v `pwd`:/srv/ \
		-it k8s_user:${VERSION} \
		bash


clean: build
	docker run \
		-v `pwd`:/srv/ \
		-it k8s_user:${VERSION} \
		bash -c "rm -rf .coverage reports/ .pytest_cache/ \
			&& find . -name '*.pyc' -exec rm -f {} \;"
