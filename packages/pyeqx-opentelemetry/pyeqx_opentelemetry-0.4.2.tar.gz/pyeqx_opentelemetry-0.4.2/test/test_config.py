from unittest import TestCase

from pyeqx.opentelemetry.config import (
    TelemetryConfiguration,
    TelemetryMetricConfiguration,
    TelemetryTraceConfiguration,
    TelemetryType,
)
from pyeqx.opentelemetry.constants import (
    DEFAULT_OTLP_ENDPOINT,
    DEFAULT_OTLP_METRIC_HTTP_ENDPOINT,
    DEFAULT_OTLP_PROTOCOL,
    DEFAULT_OTLP_TRACE_HTTP_ENDPOINT,
)


class TestConfig(TestCase):
    def test_instantiate_should_success(self):
        # act
        config = TelemetryConfiguration(
            service_name="test-service",
        )

        # assert
        self.assertIsNotNone(config)
        self.assertEqual(config.service_name, "test-service")
        self.assertEqual(config.type, TelemetryType.OTLP)
        self.assertEqual(config.endpoint, DEFAULT_OTLP_ENDPOINT)
        self.assertEqual(config.protocol, DEFAULT_OTLP_PROTOCOL)
        self.assertIsNotNone(config.trace)
        self.assertIsNotNone(config.metric)
        self.assertEqual(config.trace.endpoint, DEFAULT_OTLP_ENDPOINT)
        self.assertEqual(config.trace.protocol, DEFAULT_OTLP_PROTOCOL)
        self.assertEqual(config.metric.endpoint, DEFAULT_OTLP_ENDPOINT)
        self.assertEqual(config.metric.protocol, DEFAULT_OTLP_PROTOCOL)

    def test_instantiate_with_otlp_http_and_default_endpoint_should_success(self):
        # act
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.OTLP,
            protocol="http",
        )

        # assert
        self.assertIsNotNone(config)
        self.assertEqual(config.service_name, "test-service")
        self.assertEqual(config.type, TelemetryType.OTLP)
        self.assertEqual(config.endpoint, DEFAULT_OTLP_ENDPOINT)
        self.assertEqual(config.protocol, "http")
        self.assertIsNotNone(config.trace)
        self.assertIsNotNone(config.metric)
        self.assertEqual(config.trace.endpoint, DEFAULT_OTLP_TRACE_HTTP_ENDPOINT)
        self.assertEqual(config.trace.protocol, "http")
        self.assertEqual(config.metric.endpoint, DEFAULT_OTLP_METRIC_HTTP_ENDPOINT)
        self.assertEqual(config.metric.protocol, "http")

    def test_instantiate_with_otlp_http_and_custom_endpoint_should_success(self):
        # arrange
        endpoint = "http://opentelemetry-collector"

        # act
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.OTLP,
            endpoint=endpoint,
            protocol="http",
        )

        # assert
        self.assertIsNotNone(config)
        self.assertEqual(config.service_name, "test-service")
        self.assertEqual(config.type, TelemetryType.OTLP)
        self.assertEqual(config.endpoint, endpoint)
        self.assertEqual(config.protocol, "http")
        self.assertIsNotNone(config.trace)
        self.assertIsNotNone(config.metric)
        self.assertEqual(config.trace.endpoint, endpoint)
        self.assertEqual(config.trace.protocol, "http")
        self.assertEqual(config.metric.endpoint, endpoint)
        self.assertEqual(config.metric.protocol, "http")

    def test_instantiate_with_otlp_http_and_custom_endpoint_trace_and_metric_should_success(
        self,
    ):
        # act
        trace_config = TelemetryTraceConfiguration(
            endpoint="http://localhost:4318/v1/traces",
            protocol="http",
        )
        metric_config = TelemetryMetricConfiguration(
            endpoint="http://localhost:4318/v1/metrics",
            protocol="http",
        )

        # act
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.OTLP,
            protocol="http",
            trace=trace_config,
            metric=metric_config,
        )

        # assert
        self.assertIsNotNone(config)
        self.assertEqual(config.service_name, "test-service")
        self.assertEqual(config.type, TelemetryType.OTLP)
        self.assertEqual(config.endpoint, DEFAULT_OTLP_ENDPOINT)
        self.assertEqual(config.protocol, "http")
        self.assertIsNotNone(config.trace)
        self.assertIsNotNone(config.metric)
        self.assertEqual(config.trace.endpoint, trace_config.endpoint)
        self.assertEqual(config.trace.protocol, trace_config.protocol)
        self.assertEqual(config.metric.endpoint, metric_config.endpoint)
        self.assertEqual(config.metric.protocol, metric_config.protocol)

    def test_instantiate_with_azure_monitor_should_success(self):
        # act
        connection_string = "InstrumentationKey=00000000-0000-0000-0000-000000000000"

        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.AZURE_MONITOR,
            endpoint=connection_string,
        )

        # assert
        self.assertIsNotNone(config)
        self.assertEqual(config.service_name, "test-service")
        self.assertEqual(config.type, TelemetryType.AZURE_MONITOR)
        self.assertEqual(
            config.endpoint,
            connection_string,
        )
        self.assertIsNone(config.protocol)
        self.assertIsNotNone(config.trace)
        self.assertIsNotNone(config.metric)
        self.assertEqual(config.trace.endpoint, connection_string)
        self.assertEqual(config.trace.protocol, None)
        self.assertEqual(config.metric.endpoint, connection_string)
        self.assertEqual(config.metric.protocol, None)
