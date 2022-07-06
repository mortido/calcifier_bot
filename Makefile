IMAGE=calcifier_bot

build:
	docker build -t $(IMAGE) .

run:	build
	docker run --rm -it $(IMAGE) -v /mnt/persistent:/usr/src/app/persistent bash

