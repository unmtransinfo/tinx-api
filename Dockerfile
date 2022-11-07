FROM python:3.8.2
ENV PYTHONUNBUFFERED 1

RUN mkdir /tinx

RUN apt-get -y update
RUN apt-get install -y openssl
RUN apt-get install -y python3 python3-pip python3-dev default-libmysqlclient-dev python3-venv

COPY cloud-requirements.txt /tinx/cloud-requirements.txt

SHELL ["/bin/bash", "-c"]
RUN python3 -m venv /tinx/venv
RUN source /tinx/venv/bin/activate

RUN python --version
RUN pip --version

RUN pip install --upgrade pip setuptools==45.2.0 wheel
RUN pip install --upgrade django==1.11.17
RUN pip install -r /tinx/cloud-requirements.txt

WORKDIR /tinx/tinxapi

EXPOSE 8000

CMD python manage.py build_solr_schema
CMD python manage.py makemigrations tinxapi
CMD python manage.py migrate --database=tcrd_meta
CMD python manage.py migrate --database=tcrd
CMD python manage.py migrate
CMD python manage.py runserver 0.0.0.0:8000
