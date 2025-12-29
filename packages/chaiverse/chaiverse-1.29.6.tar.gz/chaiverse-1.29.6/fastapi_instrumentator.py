import glob
import os
import uuid

import asgi_correlation_id
from prometheus_client import multiprocess, CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator, metrics


class FastAPIInstrumentator():
    def __init__(self, fastapi_app, config: "ChaiverseServerConfig"):
        self.fastapi_app = fastapi_app
        self.config = config

    def instrument(self):
        if self._should_instrument():
            self._instrument_prometheus()
            self._patch_prometheus_middleware()
            self._instrument_tracing()

    def _instrument_prometheus(self):
        registry = CollectorRegistry()
        instrumentator = Instrumentator(registry=registry)
        instrumentator.add(
            metrics.default(
                custom_labels=self.config.prometheus_labels,
                metric_subsystem=self.config.name,
                latency_lowr_buckets=self.config.prometheus_latency_buckets,
                registry=registry
            )
        )
        instrumentator.instrument(self.fastapi_app)
        instrumentator.expose(self.fastapi_app)

    def _instrument_tracing(self):
        self.fastapi_app.add_middleware(
            asgi_correlation_id.CorrelationIdMiddleware,
            header_name=self.config.trace_header_name,
            validator=None,
            transformer=_transform_trace_id,
        )

    def _patch_prometheus_middleware(self):
        # Change the behaviour of the instrumentation middleware so that it
        # returns fully interpolated paths in the prometheus labels instead of
        # leaving them uninterpolated
        middleware = [
            middleware for middleware in self.fastapi_app.user_middleware
            if "Prometheus" in middleware.cls.__name__
        ]
        middleware = middleware[0]
        def _get_handler(self, request):
            return request.url.path, True
        middleware.cls._get_handler = _get_handler

    def _should_instrument(self):
        # This avoids a bug on later version of fastapi where it crashes
        # if you try to add a middleware more than once (useful in testing)
        should_add_middleware = True
        if self.fastapi_app.middleware_stack is not None:
            should_add_middleware = False
        return should_add_middleware


def _transform_trace_id(trace_id):
    # https://cloud.google.com/trace/docs/trace-context
    parts = trace_id.split('-')
    if len(parts) > 1:
        trace_id = parts[1]
    return trace_id
