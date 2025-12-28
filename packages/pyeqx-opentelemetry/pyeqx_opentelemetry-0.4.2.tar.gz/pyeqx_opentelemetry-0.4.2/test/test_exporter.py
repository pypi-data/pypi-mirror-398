from unittest import TestCase
from pyeqx.opentelemetry.config import (
    TelemetryMetricConfiguration,
    TelemetryTraceConfiguration,
)
from pyeqx.opentelemetry.exporters.otlp_exporter import create_otlp_exporter


class TestExporter(TestCase):
    def test_create_otlp_exporter_with_invalid_protocol_should_raise_value_error(self):
        # act & assert
        with self.assertRaises(ValueError) as context:
            create_otlp_exporter(
                trace=TelemetryTraceConfiguration(
                    endpoint="http://example.com",
                    protocol="invalid_protocol",
                ),
                metric=TelemetryMetricConfiguration(
                    endpoint="http://example.com",
                    protocol="invalid_protocol",
                ),
            )

        self.assertEqual(
            str(context.exception),
            "Unsupported OTLP protocol: invalid_protocol",
        )

    def test_create_otlp_exporter_with_on_of_invalid_protocol_should_raise_value_error(
        self,
    ):
        # act & assert
        with self.assertRaises(ValueError) as context:
            create_otlp_exporter(
                trace=TelemetryTraceConfiguration(
                    endpoint="http://example.com",
                    protocol="http",
                ),
                metric=TelemetryMetricConfiguration(
                    endpoint="http://example.com",
                    protocol="invalid_protocol",
                ),
            )

        self.assertEqual(
            str(context.exception),
            "Unsupported OTLP protocol: invalid_protocol",
        )
