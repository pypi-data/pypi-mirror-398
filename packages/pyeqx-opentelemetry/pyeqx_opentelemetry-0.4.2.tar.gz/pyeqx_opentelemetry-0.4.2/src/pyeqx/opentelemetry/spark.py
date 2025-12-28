from typing import Any

from pyeqx.opentelemetry.config import TelemetryConfiguration, TelemetryType


def configure_spark_options(
    config: TelemetryConfiguration, spark_options: dict[str, Any] | None = None
):
    if config.type == TelemetryType.OTLP:
        return __configure_spark_with_otlp(
            config=config,
            spark_options=spark_options,
        )
    elif config.type == TelemetryType.AZURE_MONITOR:
        return __configure_spark_with_azure_monitor(
            config=config,
            spark_options=spark_options,
        )
    else:
        raise ValueError(f"Unsupported exporter type: {config.type}")


def __configure_spark_with_otlp(
    config: TelemetryConfiguration,
    spark_options: dict[str, Any] | None = None,
):
    """
    Configure Spark options for OTLP.
    """
    if spark_options is None:
        spark_options = {}

    default_executor_java_options = (
        '-javaagent:"/opt/spark/work-dir/opentelemetry-javaagent.jar"'
    )

    executor_java_options = spark_options.get(
        "spark.executor.extraJavaOptions", default_executor_java_options
    )

    spark_options.update(
        {
            "spark.executor.extraJavaOptions": executor_java_options,
            "spark.executorEnv.OTEL_RESOURCE_PROVIDERS_AZURE_ENABLED": True,
            "spark.executorEnv.OTEL_EXPORTER_OTLP_ENDPOINT": config.endpoint,
            "spark.executorEnv.OTEL_EXPORTER_OTLP_PROTOCOL": config.protocol
            or "http/protobuf",
            "spark.executorEnv.OTEL_TRACES_EXPORTER": "console,otlp",
            "spark.executorEnv.OTEL_METRICS_EXPORTER": "console,otlp",
            "spark.executorEnv.OTEL_SERVICE_NAME": config.service_name,
            "spark.executorEnv.OTEL_JAVAAGENT_DEBUG": True,
        }
    )

    return spark_options


def __configure_spark_with_azure_monitor(
    config: TelemetryConfiguration, spark_options: dict[str, Any] | None = None
):
    """
    Configure Spark options for Azure Monitor.
    """
    if spark_options is None:
        spark_options = {}

    default_executor_java_options = (
        '-javaagent:"/opt/spark/work-dir/applicationinsights-agent.jar"'
    )

    executor_java_options = spark_options.get(
        "spark.executor.extraJavaOptions", default_executor_java_options
    )

    spark_options.update(
        {
            "spark.executor.extraJavaOptions": executor_java_options,
            "spark.executorEnv.APPLICATIONINSIGHTS_CONNECTION_STRING": config.endpoint,
            "spark.executorEnv.OTEL_RESOURCE_PROVIDERS_AZURE_ENABLED": True,
            "spark.executorEnv.OTEL_TRACES_EXPORTER": "none",
            "spark.executorEnv.OTEL_METRICS_EXPORTER": "none",
            "spark.executorEnv.OTEL_LOGS_EXPORTER": "none",
            "spark.executorEnv.OTEL_SERVICE_NAME": config.service_name,
            "spark.executorEnv.OTEL_JAVAAGENT_DEBUG": True,
        }
    )

    return spark_options
