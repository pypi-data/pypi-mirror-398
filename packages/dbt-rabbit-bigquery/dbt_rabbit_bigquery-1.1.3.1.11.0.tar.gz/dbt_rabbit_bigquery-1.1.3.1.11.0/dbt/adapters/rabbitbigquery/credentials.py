"""
Rabbit BigQuery Credentials Module

This module extends dbt's BigQuery credentials to include Rabbit-specific
configuration for automatic job optimization.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Union

from dbt.adapters.bigquery import BigQueryCredentials


@dataclass
class RabbitBigQueryCredentials(BigQueryCredentials):
    """
    Extended BigQuery credentials with Rabbit API configuration for job optimization.

    This class extends the standard BigQueryCredentials to add Rabbit-specific
    configuration options for automatic cost optimization. All standard BigQuery
    credential fields are supported.

    Attributes:
        rabbit_api_key: API key for Rabbit authentication. Required for optimization.
        rabbit_base_url: Custom Rabbit API base URL. Defaults to production endpoint.
        rabbit_default_pricing_mode: Default pricing mode for queries. Options:
            - "on_demand"
            - "slot_based"
        rabbit_reservation_ids: List of BigQuery reservation IDs to consider for
            optimization. Can be provided as comma-separated string or list.
            Format: "project-id:location.reservation-name"
        rabbit_enabled: Enable/disable Rabbit optimization. Useful for testing
            or temporarily disabling optimization without changing configuration.

    Example:
        >>> creds = RabbitBigQueryCredentials(
        ...     project='my-project',
        ...     dataset='my_dataset',
        ...     rabbit_api_key='rb_abc123',
        ...     rabbit_default_pricing_mode='on_demand',
        ...     rabbit_reservation_ids='my-project:us.res1,my-project:eu.res2'
        ... )
    """

    # Rabbit API configuration
    rabbit_api_key: Optional[str] = None
    rabbit_base_url: Optional[str] = None
    rabbit_default_pricing_mode: Optional[str] = "on_demand"
    rabbit_reservation_ids: Union[List[str], str] = field(default_factory=list)
    rabbit_enabled: bool = True  # Allow disabling optimization if needed

    def __post_init__(self):
        """
        Post-initialization processing for Rabbit credentials.

        Handles conversion of reservation IDs from various input formats
        (comma-separated string, list) into a consistent list format.
        This ensures downstream code always works with List[str].
        """
        super().__post_init__()

        # Handle comma-separated string input for reservation IDs
        # This runs after mashumaro deserialization
        if isinstance(self.rabbit_reservation_ids, str):
            if self.rabbit_reservation_ids:
                self.rabbit_reservation_ids = [r.strip() for r in self.rabbit_reservation_ids.split(",") if r.strip()]
            else:
                self.rabbit_reservation_ids = []
        elif isinstance(self.rabbit_reservation_ids, list):
            # Check if it was incorrectly split into characters
            if len(self.rabbit_reservation_ids) > 0 and len(self.rabbit_reservation_ids[0]) == 1:
                # It was split into characters, rejoin and resplit
                joined = "".join(self.rabbit_reservation_ids)
                self.rabbit_reservation_ids = [r.strip() for r in joined.split(",") if r.strip()]

    @property
    def type(self):
        """Return the adapter type identifier for dbt."""
        return "rabbitbigquery"

    @property
    def unique_field(self):
        """Return the field that uniquely identifies this connection."""
        return self.database

    def _connection_keys(self):
        """
        Return tuple of credential fields used for connection identity.

        These keys determine when dbt should reuse vs. create new connections.
        Includes both standard BigQuery keys and Rabbit-specific configuration.

        Returns:
            Tuple of field names that identify a unique connection.
        """
        # Get parent connection keys
        keys = super()._connection_keys()

        # Add Rabbit-specific keys
        return keys + (
            "rabbit_api_key",
            "rabbit_base_url",
            "rabbit_default_pricing_mode",
            "rabbit_reservation_ids",
            "rabbit_enabled",
        )
