FROM python:3.8-slim

COPY . /srv/
WORKDIR /srv/

RUN pip install .[test]

CMD pytest -vv tests/