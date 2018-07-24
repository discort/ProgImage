FROM python:3.6

RUN mkdir /var/app
WORKDIR /var/app

COPY image_processing /var/app/image_processing

COPY services/rotation/requirements.txt /var/app/requirements.txt
RUN pip install -r /var/app/requirements.txt --no-cache-dir

COPY services/rotation /var/app

EXPOSE 8081

ENTRYPOINT ["python", "api.py"]