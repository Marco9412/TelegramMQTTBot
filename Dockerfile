FROM python:3-alpine3.10

WORKDIR /usr/src/app
ENV PYTHONPATH app

COPY requirements.txt ./
RUN apk update --no-cache && apk add gcc musl-dev libffi-dev openssl-dev --no-cache
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "app/__main__.py", "./resources/settings.json" ]
