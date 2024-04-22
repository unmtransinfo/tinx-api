FROM python:3.8.2
ENV PYTHONUNBUFFERED 1

RUN mkdir /tinx

RUN apt-get -y update
RUN apt-get install -y openssl
RUN apt-get install -y python3 python3-pip python3-dev default-libmysqlclient-dev python3-venv

SHELL ["/bin/bash", "-c"]
RUN python3 -m venv /tinx/venv
RUN source /tinx/venv/bin/activate

RUN pip install --upgrade pip setuptools==45.2.0 wheel
RUN pip install --upgrade django==1.11.17

COPY . /tinx
RUN pip install -r /tinx/cloud-requirements.txt
WORKDIR /tinx/tinxapi
EXPOSE 8000

RUN python manage.py build_solr_schema
RUN python manage.py makemigrations

CMD sh -c "python manage.py migrate --database=tcrd_meta && python manage.py migrate --database=tcrd && python manage.py migrate && python tinxapi/metadata.py && python manage.py runserver 0.0.0.0:8000"
