IMAGE=calcifier_bot

build:
	docker build -t $(IMAGE) .

run:	build
	docker run --rm -v /mnt/persistent:/usr/src/app/persistent $(IMAGE)

