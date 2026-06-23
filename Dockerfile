# TODO: will need to upgrade from python 3.8 (it is no longer supported)
FROM python:3.8-bullseye
ENV PYTHONUNBUFFERED=1

RUN mkdir /tinx

RUN apt-get -y update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY . /tinx
RUN pip install --no-cache-dir -r /tinx/requirements.txt
WORKDIR /tinx/tinxapi
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py build_solr_schema && python manage.py runserver 0.0.0.0:8000"]