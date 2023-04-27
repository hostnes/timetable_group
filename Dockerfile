FROM python:3.9

COPY . /workdir

COPY requirements.txt /temp/requirements.txt

RUN pip install -r /temp/requirements.txt

EXPOSE 8000

WORKDIR /workdir
