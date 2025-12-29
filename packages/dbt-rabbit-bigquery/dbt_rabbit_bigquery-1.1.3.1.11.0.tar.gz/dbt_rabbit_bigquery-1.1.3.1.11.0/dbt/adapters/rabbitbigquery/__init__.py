"""
dbt-rabbit-bigquery: BigQuery adapter with automatic cost optimization

This adapter extends dbt-bigquery to provide transparent cost optimization
for all BigQuery queries via the Rabbit API. It's a drop-in replacement that
requires minimal configuration changes.

Usage:
    Install via pip:
        pip install dbt-rabbit-bigquery

    Configure in profiles.yml:
        type: rabbitbigquery
        rabbit_api_key: "{{ env_var('RABBIT_API_KEY') }}"
        rabbit_default_pricing_mode: on_demand
        rabbit_reservation_ids: "project:us.reservation1"

For more information:
    - Repository: https://github.com/followtherabbit/dbt-rabbit-bigquery
    - Documentation: https://followrabbit.ai
    - Support: success@followrabbit.ai
"""

from dbt.adapters.rabbitbigquery.connections import RabbitBigQueryConnectionManager
from dbt.adapters.rabbitbigquery.credentials import RabbitBigQueryCredentials
from dbt.adapters.rabbitbigquery.impl import RabbitBigQueryAdapter
from dbt.adapters.rabbitbigquery.__version__ import version

from dbt.adapters.base import AdapterPlugin
from dbt.include import rabbitbigquery

# Define the dbt adapter plugin
Plugin = AdapterPlugin(
    adapter=RabbitBigQueryAdapter,  # type: ignore[arg-type]
    credentials=RabbitBigQueryCredentials,
    include_path=rabbitbigquery.PACKAGE_PATH,
)

__version__ = version

__all__ = [
    "RabbitBigQueryAdapter",
    "RabbitBigQueryConnectionManager",
    "RabbitBigQueryCredentials",
    "Plugin",
    "__version__",
]
