from dataclasses import dataclass
from enum import Enum

from pyeqx.opentelemetry.constants import (
    DEFAULT_OTLP_ENDPOINT,
    DEFAULT_OTLP_METRIC_HTTP_ENDPOINT,
    DEFAULT_OTLP_PROTOCOL,
    DEFAULT_OTLP_TRACE_HTTP_ENDPOINT,
)


class TelemetryType(str, Enum):
    OTLP = "otlp"
    AZURE_MONITOR = "azuremonitor"


@dataclass
class TelemetryTraceConfiguration:
    endpoint: str
    protocol: str

    def __init__(self, endpoint: str, protocol: str):
        self.endpoint = endpoint
        self.protocol = protocol


@dataclass
class TelemetryMetricConfiguration:
    endpoint: str
    protocol: str

    def __init__(self, endpoint: str, protocol: str):
        self.endpoint = endpoint
        self.protocol = protocol


@dataclass
class TelemetryConfiguration:
    service_name: str
    type: TelemetryType
    endpoint: str
    protocol: str
    trace: TelemetryTraceConfiguration
    metric: TelemetryMetricConfiguration

    def __init__(
        self,
        service_name: str,
        type: TelemetryType = TelemetryType.OTLP,
        endpoint: str = None,
        protocol: str = None,
        trace: TelemetryTraceConfiguration = None,
        metric: TelemetryMetricConfiguration = None,
    ):
        self.service_name = service_name
        self.type = type

        if type == TelemetryType.OTLP:
            self.endpoint = endpoint or DEFAULT_OTLP_ENDPOINT
            self.protocol = protocol or DEFAULT_OTLP_PROTOCOL

            self.trace = self.__build_trace_config(config=trace)
            self.metric = self.__build_metric_config(config=metric)
        else:
            self.endpoint = endpoint
            self.protocol = None

            self.trace = TelemetryTraceConfiguration(
                endpoint=endpoint,
                protocol=None,
            )
            self.metric = TelemetryMetricConfiguration(
                endpoint=endpoint,
                protocol=None,
            )

    def __build_trace_config(self, config: TelemetryTraceConfiguration | None):
        if config is None:
            endpoint = self.endpoint

            if self.protocol == "http":
                if endpoint.startswith("http://") or endpoint.startswith("https://"):
                    endpoint = endpoint
                else:
                    endpoint = DEFAULT_OTLP_TRACE_HTTP_ENDPOINT
            else:
                endpoint = self.endpoint

            return TelemetryTraceConfiguration(
                endpoint=endpoint,
                protocol=self.protocol,
            )
        else:
            return config

    def __build_metric_config(self, config: TelemetryMetricConfiguration | None):
        if config is None:
            endpoint = self.endpoint

            if self.protocol == "http":
                if endpoint.startswith("http://") or endpoint.startswith("https://"):
                    endpoint = endpoint
                else:
                    endpoint = DEFAULT_OTLP_METRIC_HTTP_ENDPOINT
            else:
                endpoint = self.endpoint

            return TelemetryMetricConfiguration(
                endpoint=endpoint,
                protocol=self.protocol,
            )
        else:
            return config
