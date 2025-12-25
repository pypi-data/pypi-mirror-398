import contextlib
import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setting_otlp(
    app: FastAPI,
    app_name: str,
    endpoint: str,
) -> None:
    try:
        from opentelemetry import trace  # type: ignore[import-not-found]
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[import-not-found]
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore[import-not-found]

        # Setting OpenTelemetry
        # set the service name to show in traces
        resource = Resource.create(
            attributes={
                'service.name': app_name,
                'compose_service': app_name,
            },
        )

        # set the tracer provider
        tracer = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer)
        tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    except ImportError:
        logger.warning('OpenTelemetry is not installed. Skipping OpenTelemetry setup.')
        return

    with contextlib.suppress(ImportError):
        from opentelemetry.instrumentation.logging import LoggingInstrumentor  # type: ignore[import-not-found]

        LoggingInstrumentor().instrument(set_logging_format=True)

    with contextlib.suppress(ImportError):
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-not-found]

        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)

    with contextlib.suppress(ImportError):
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor  # type: ignore[import-not-found]

        PsycopgInstrumentor().instrument(enable_commenter=True, commenter_options={})

    with contextlib.suppress(ImportError):
        from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore[import-not-found]

        RequestsInstrumentor().instrument(tracer_provider=tracer)

    with contextlib.suppress(ImportError):
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor  # type: ignore[import-not-found]

        HTTPXClientInstrumentor().instrument()
