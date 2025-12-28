from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as OTLPHttpSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as OTLPHttpMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as OTLPGrpcSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter as OTLPGrpcMetricExporter,
)

from pyeqx.opentelemetry.config import (
    TelemetryMetricConfiguration,
    TelemetryTraceConfiguration,
)


def create_otlp_exporter(
    trace: TelemetryTraceConfiguration, metric: TelemetryMetricConfiguration
):
    trace_exporter = __build_trace_exporter(config=trace)
    metric_exporter = __build_metric_exporter(config=metric)

    return trace_exporter, metric_exporter


def __build_trace_exporter(config: TelemetryTraceConfiguration):
    if config.protocol == "grpc":
        return OTLPGrpcSpanExporter(endpoint=config.endpoint)
    elif config.protocol == "http":
        return OTLPHttpSpanExporter(endpoint=config.endpoint)
    else:
        raise ValueError(f"Unsupported OTLP protocol: {config.protocol}")


def __build_metric_exporter(config: TelemetryMetricConfiguration):

    if config.protocol == "grpc":
        return OTLPGrpcMetricExporter(endpoint=config.endpoint)
    elif config.protocol == "http":
        return OTLPHttpMetricExporter(endpoint=config.endpoint)
    else:
        raise ValueError(f"Unsupported OTLP protocol: {config.protocol}")
