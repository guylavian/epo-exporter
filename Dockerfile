FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USER=app \
    HOME=/home/app

# Install curl for HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos "" --home ${HOME} ${USER}

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN pip install --no-cache-dir .

USER ${USER}

EXPOSE 9898
# Prefer liveness-only check to avoid restart if ePO is temporarily unavailable
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD curl -fsS http://127.0.0.1:9898/healthz || exit 1

# Safe startup even without console-script installed
ENTRYPOINT ["python", "-m", "epo_exporter"]
CMD ["--web.listen-address", ":9898"]


