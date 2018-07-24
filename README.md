# ProgImage

Programmatic image storage

## Getting started

ProgImage is a Python 3.6 API backend that runs on Docker. Go to [docker.com](https://www.docker.com/)
to download and install Docker.

1. Start up the Docker containers:

	`docker-compose up`

2. To upload a new image:

	```
	POST http://localhost:8080/images
	Content-Type: image/jpeg
	Content-Length: 55058

	b'<binary image data>'
	```
3. To get an existing image:

	```
	GET http://localhost:8080/images/<image_id>
	Content-Type: application/json

	b''
	```

4. To rotate an image:

	```
	POST http://localhost:8081/rotate
	Content-Type: application/json
	Content-Length: 67

	b'{"image_id": "<image_id>", "angle": "90"}'
	```

5. To resize an image:

	```
	POST http://localhost:8082/resize
	Content-Type: application/json
	Content-Length: 85

	b'{"image_id": "<image_id>", "height": "100", "width": "100"}'
	```

> Note:
> * Currently port 27017 on the mongoDB container will be bound to 27017 on localhost. If this port is already in use by something else on localhost, you'll experience issues.

## Running tests

To run the tests, run the following command:

	docker-compose exec storage_api py.test tests.py