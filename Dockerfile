FROM python:3.7.7

ADD . /yatube

ENV DJANGO_SETTINGS_MODULE yatube.settings

LABEL Valentin Guniakov "radioval87@yandex.ru"

COPY ./requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt

COPY . /app

WORKDIR /app

CMD python3 /yatube/manage.py runserver 0.0.0.0:8000
