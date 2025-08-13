FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USER=app \
    HOME=/home/app

RUN adduser --disabled-password --gecos "" --home ${HOME} ${USER}
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN pip install --no-cache-dir .

USER ${USER}

EXPOSE 9898

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD wget -qO- http://127.0.0.1:9898/healthz || exit 1

ENTRYPOINT ["epo-exporter"]
CMD ["--web.listen-address", ":9898"]


