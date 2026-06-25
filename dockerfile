FROM python:3.12

COPY ./requirements.txt /bibip/requirements.txt
RUN pip install -r /bibip/requirements.txt

COPY ./src /bibip/src
COPY ./tests /bibip/tests

ENV PYTHONPATH "${PYTHONPATH}:/bibip:/bibip/src"

WORKDIR /bibip
CMD ["tail", "-f", "/dev/null"]
