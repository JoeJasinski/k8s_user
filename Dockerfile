FROM python:3.8-slim

COPY tests/requirements.txt /
RUN pip install -r /requirements.txt

COPY . /srv/
WORKDIR /srv/

RUN pip install .[test]

CMD pytest -vv tests/