VERSION ?= "1.0.0"

build:
	#poetry install
	docker build -t k8s_user:${VERSION} . 


test: build
	docker run -it k8s_user:${VERSION}
