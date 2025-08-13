from __future__ import annotations

from typing import Callable

from prometheus_client import make_wsgi_app
from prometheus_client.core import CollectorRegistry
from wsgiref.simple_server import make_server
from .health import is_ready


def serve_http(host: str, port: int, telemetry_path: str, registry: CollectorRegistry) -> None:
    metrics_app = make_wsgi_app(registry)

    def app(environ, start_response):
        path = environ.get("PATH_INFO", "") or "/"
        if path == telemetry_path:
            return metrics_app(environ, start_response)
        if path in ("/", "/healthz"):
            start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"ok\n"]
        if path in ("/ready", "/-/ready"):
            code = "200 OK" if is_ready() else "503 Service Unavailable"
            start_response(code, [("Content-Type", "text/plain; charset=utf-8")])
            return [b"ready\n" if code.startswith("200") else b"not ready\n"]
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"not found\n"]

    httpd = make_server(host, port, app)
    httpd.serve_forever()


