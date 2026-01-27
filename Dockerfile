FROM python:3.14.2

WORKDIR /app


COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app

EXPOSE 502/tcp

ENTRYPOINT [ "python", "./main.py" ]
#CMD [ "--host", "0.0.0.0", "--port", "502" ]

