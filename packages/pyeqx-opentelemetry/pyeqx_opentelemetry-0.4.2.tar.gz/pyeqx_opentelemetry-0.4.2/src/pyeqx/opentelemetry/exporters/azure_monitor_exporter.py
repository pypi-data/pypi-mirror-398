from azure.monitor.opentelemetry.exporter import (
    AzureMonitorTraceExporter,
    AzureMonitorMetricExporter,
    AzureMonitorLogExporter,
)


def create_azure_monitor_exporter(connection_string: str):
    return (
        AzureMonitorTraceExporter(connection_string=connection_string),
        AzureMonitorMetricExporter(connection_string=connection_string),
        AzureMonitorLogExporter(connection_string=connection_string),
    )
