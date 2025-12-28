from opentelemetry import trace, metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from pyeqx.opentelemetry.config import TelemetryConfiguration, TelemetryType
from pyeqx.opentelemetry.exporters import (
    create_otlp_exporter,
    create_azure_monitor_exporter,
)


def initialize_telemetry(config: TelemetryConfiguration, is_debug: bool = False):
    resource = Resource(attributes={SERVICE_NAME: config.service_name})

    if config.type == TelemetryType.OTLP:
        trace_exporter, metric_exporter = create_otlp_exporter(
            trace=config.trace,
            metric=config.metric,
        )
    elif config.type == TelemetryType.AZURE_MONITOR:
        trace_exporter, metric_exporter, log_provider = create_azure_monitor_exporter(
            connection_string=config.endpoint
        )
    else:
        raise ValueError(f"Unsupported exporter type: {config.type}")

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(metric_exporter)],
    )

    trace.set_tracer_provider(tracer_provider)
    metrics.set_meter_provider(meter_provider)

    return (
        tracer_provider,
        meter_provider,
        log_provider if config.type == TelemetryType.AZURE_MONITOR else None,
    )
