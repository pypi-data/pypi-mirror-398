from unittest import TestCase
from dotenv import load_dotenv

from pyeqx.opentelemetry.config import TelemetryConfiguration, TelemetryType
from pyeqx.opentelemetry.spark import configure_spark_options


load_dotenv()


class TestSpark(TestCase):
    def test_configure_spark_with_otlp(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
        )
        expected_spark_options = {
            "spark.executor.extraJavaOptions": '-javaagent:"/opt/spark/work-dir/opentelemetry-javaagent_2.15.0.jar"',
            "spark.executorEnv.OTEL_RESOURCE_PROVIDERS_AZURE_ENABLED": True,
            "spark.executorEnv.OTEL_EXPORTER_OTLP_ENDPOINT": config.endpoint,
            "spark.executorEnv.OTEL_EXPORTER_OTLP_PROTOCOL": config.protocol
            or "http/protobuf",
            "spark.executorEnv.OTEL_TRACES_EXPORTER": "console,otlp",
            "spark.executorEnv.OTEL_METRICS_EXPORTER": "console,otlp",
            "spark.executorEnv.OTEL_SERVICE_NAME": config.service_name,
            "spark.executorEnv.OTEL_JAVAAGENT_DEBUG": True,
        }

        # act
        actual_spark_options = configure_spark_options(config=config)

        # assert
        self.assertIsNotNone(actual_spark_options)

        for key, value in expected_spark_options.items():
            self.assertEqual(actual_spark_options[key], value)

    def test_configure_spark_with_azure_monitor(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.AZURE_MONITOR,
        )
        expected_spark_options = {
            "spark.executor.extraJavaOptions": '-javaagent:"/opt/spark/work-dir/applicationinsights-agent_3.7.2.jar"',
            "spark.executorEnv.APPLICATIONINSIGHTS_CONNECTION_STRING": config.endpoint,
            "spark.executorEnv.OTEL_RESOURCE_PROVIDERS_AZURE_ENABLED": True,
            "spark.executorEnv.OTEL_TRACES_EXPORTER": "none",
            "spark.executorEnv.OTEL_METRICS_EXPORTER": "none",
            "spark.executorEnv.OTEL_LOGS_EXPORTER": "none",
            "spark.executorEnv.OTEL_SERVICE_NAME": config.service_name,
            "spark.executorEnv.OTEL_JAVAAGENT_DEBUG": True,
        }

        # act
        actual_spark_options = configure_spark_options(config=config)

        # assert
        self.assertIsNotNone(actual_spark_options)

        for key, value in expected_spark_options.items():
            self.assertEqual(actual_spark_options[key], value)

    def test_configure_spark_with_unsupported_type(self):
        # arrange
        config = TelemetryConfiguration(
            service_name="test-service",
            type=TelemetryType.OTLP,
        )

        # act & assert
        with self.assertRaises(ValueError) as context:
            config.type = "unsupported_type"
            configure_spark_options(config=config)

        self.assertEqual(
            str(context.exception),
            "Unsupported exporter type: unsupported_type",
        )
