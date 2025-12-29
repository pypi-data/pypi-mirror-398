"""
Rabbit BigQuery Adapter Implementation

This module provides the main adapter class that integrates Rabbit optimization
with dbt's BigQuery adapter.
"""

from dbt.adapters.bigquery import BigQueryAdapter
from dbt.adapters.rabbitbigquery.connections import RabbitBigQueryConnectionManager


class RabbitBigQueryAdapter(BigQueryAdapter):
    """
    dbt adapter for BigQuery with automatic Rabbit cost optimization.

    This adapter extends the standard BigQueryAdapter to provide transparent
    cost optimization through the Rabbit API. It is a drop-in replacement
    for dbt-bigquery with no changes required to dbt models or project structure.

    The adapter inherits all BigQuery functionality from dbt-bigquery and adds:
        - Automatic query routing to optimal BigQuery pricing models
        - Cost-aware reservation assignment
        - Real-time optimization via Rabbit API
        - Graceful fallback on optimization failures

    Usage:
        Configure in profiles.yml:

        ```yaml
        my_project:
          outputs:
            dev:
              type: rabbitbigquery  # Changed from 'bigquery'
              # ... standard BigQuery configuration ...
              rabbit_api_key: "{{ env_var('RABBIT_API_KEY') }}"
              rabbit_default_pricing_mode: on_demand
              rabbit_reservation_ids: "project:us.reservation1"
        ```

    Note:
        All optimization logic is implemented in RabbitBigQueryConnectionManager.
        This class primarily serves as the adapter entry point for dbt.
    """

    ConnectionManager = RabbitBigQueryConnectionManager

    @classmethod
    def type(cls):
        """
        Return adapter type identifier.

        Note: This should return 'rabbitbigquery' to match the profile configuration.
        The adapter will use rabbitbigquery__ prefixed macros that we sync from bigquery.
        """
        return "rabbitbigquery"
