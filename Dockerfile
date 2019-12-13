FROM python:2.7.17-buster
ENV PYTHONUNBUFFERED 1

RUN mkdir /tinx

RUN apt-get -y update
RUN apt-get install -y \
	python \ 
	python-pip \ 
	python-dev \
	default-libmysqlclient-dev \
	virtualenv

COPY cloud-requirements.txt /tinx/cloud-requirements.txt

RUN pip install -r /tinx/cloud-requirements.txt

WORKDIR /tinx/tinxapi

EXPOSE 8000

CMD python manage.py migrate
CMD python manage.py runserver 0.0.0.0:8000
