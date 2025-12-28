import os
from dotenv import load_dotenv
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from unittest import TestCase

from pyeqx.opentelemetry.config import TelemetryConfiguration, TelemetryType
from pyeqx.opentelemetry.instrumentation import initialize_telemetry

load_dotenv()


class TestInstrumentation(TestCase):
    __tracer_provider: TracerProvider
    __metric_provider: MeterProvider

    def test_initialize_telemetry_should_success(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
        )

        # act
        tracer_provider, metric_provider, log_provider = initialize_telemetry(
            config=config
        )

        self.__tracer_provider = tracer_provider
        self.__metric_provider = metric_provider

        # assert
        self.assertIsNotNone(tracer_provider)
        self.assertIsNotNone(metric_provider)

    def test_initialize_telemetry_with_otlp_http_should_success(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.OTLP,
            endpoint=os.environ.get("OTLP_METRICS_HTTP_ENDPOINT", ""),
            protocol="http",
        )

        # act
        tracer_provider, metric_provider, log_provider = initialize_telemetry(
            config=config
        )

        # assert
        self.assertIsNotNone(tracer_provider)
        self.assertIsNotNone(metric_provider)

    def test_initialize_telemetry_with_azure_monitor_should_success(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.AZURE_MONITOR,
            endpoint=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", ""),
        )

        # act
        tracer_provider, metric_provider, log_provider = initialize_telemetry(
            config=config
        )

        # assert
        self.assertIsNotNone(tracer_provider)
        self.assertIsNotNone(metric_provider)

    def test_initialize_telemetry_with_unsupported_otlp_protocol_should_raise_error(
        self,
    ):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.OTLP,
            endpoint=os.environ.get("OTLP_METRICS_HTTP_ENDPOINT", ""),
            protocol="unsupported_protocol",
        )

        # act & assert
        with self.assertRaises(ValueError) as context:
            initialize_telemetry(config=config)

        self.assertEqual(
            str(context.exception),
            "Unsupported OTLP protocol: unsupported_protocol",
        )

    def test_initialize_telemetry_with_invalid_type_should_raise_error(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
            type="invalid_type",  # Invalid type
        )

        # act & assert
        with self.assertRaises(ValueError) as context:
            initialize_telemetry(config=config)

        self.assertEqual(
            str(context.exception),
            "Unsupported exporter type: invalid_type",
        )
