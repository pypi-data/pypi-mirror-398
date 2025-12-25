from pydantic.dataclasses import dataclass

from ....warehouse.bigquery import BigQueryCredentials


@dataclass
class CountCredentials(BigQueryCredentials):
    """Count credentials extending BigQuery credentials with additional dataset information"""

    dataset_id: str
