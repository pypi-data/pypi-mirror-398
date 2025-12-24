from enum import Enum


class MetricUnit(Enum):
    Count = "Count"
    Milliseconds = "Milliseconds"
    Percent = "Percent"


def create_metric_context(
    type: str, apiname: str, operation: str, value, unit: MetricUnit
):
    return {
        "MetricName": type,
        "MetricValue": value,
        "MetricUnit": unit.value,
        "Dimensions": [
            {
                "Operation": operation,
            },
            {
                "ApiName": apiname,
            },
        ],
    }
