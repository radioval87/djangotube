IMAGE_NAME = yatube
VERSION = latest

build:
	docker build -t $(IMAGE_NAME):$(VERSION) .
run:
	docker run -it -p 8000:8000 --rm --name yatube $(IMAGE_NAME):$(VERSION)
lint:
	docker run --rm -v $(PWD):/code eeacms/pylint
	