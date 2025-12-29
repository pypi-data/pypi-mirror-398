"""
Rabbit BigQuery Connection Manager

This module handles BigQuery connections and intercepts query execution to apply
Rabbit's cost optimization via monkey-patching the BigQuery client's query method.
"""

import json
import re
from dataclasses import asdict
from dbt.adapters.events.logging import AdapterLogger

from dbt.adapters.bigquery.connections import BigQueryConnectionManager
from dbt.adapters.rabbitbigquery.credentials import RabbitBigQueryCredentials
from rabbit_bq_job_optimizer import RabbitBQJobOptimizer, OptimizationConfig

# Configure logger for dbt integration
_logger = AdapterLogger("RabbitBigQuery")


class RabbitBigQueryConnectionManager(BigQueryConnectionManager):
    """
    Extended BigQuery connection manager with Rabbit optimization.

    This class extends the standard BigQueryConnectionManager to intercept
    BigQuery job submissions and apply cost optimization via the Rabbit API.

    The optimization is implemented via monkey-patching the BigQuery client's
    `query()` method, ensuring all queries (including those from dbt's internal
    operations) are optimized transparently.

    Key Features:
        - Automatic job configuration optimization
        - Graceful fallback on API errors
        - Comprehensive logging at DEBUG/INFO/WARNING levels
        - No impact on dbt functionality

    Attributes:
        TYPE: Adapter type identifier ("rabbitbigquery")
        RABBIT_PATCHED_MARKER: Internal marker to prevent double-patching
    """

    TYPE = "rabbitbigquery"
    RABBIT_PATCHED_MARKER = "_rabbit_patched"

    @classmethod
    def open(cls, connection):
        """
        Open BigQuery connection and apply Rabbit optimization patch.

        This method:
        1. Opens the standard BigQuery connection
        2. Validates Rabbit configuration
        3. Monkey-patches the BigQuery client's query method
        4. Ensures patch is applied only once per client

        Args:
            connection: dbt connection object to open

        Returns:
            The opened connection with Rabbit optimization applied (if configured)

        Note:
            If Rabbit configuration is incomplete or invalid, returns an unmodified
            connection and logs a warning. dbt execution continues normally.
        """
        connection = super().open(connection)

        creds = connection.credentials
        if not isinstance(creds, RabbitBigQueryCredentials):
            _logger.warning("Rabbit optimization disabled: Invalid credentials type. Expected RabbitBigQueryCredentials.")
            return connection

        if not creds.rabbit_enabled:
            _logger.warning("Rabbit optimization disabled: rabbit_enabled is set to False")
            return connection

        if not creds.rabbit_api_key:
            _logger.warning("Rabbit optimization disabled: Missing required rabbit_api_key")
            return connection

        if not creds.rabbit_reservation_ids:
            _logger.warning("Rabbit optimization disabled: Missing required rabbit_reservation_ids")
            return connection

        # Validate reservation ID format: admin_project:region.reservation_name
        # Pattern: project-id:location.reservation-name (e.g., my-project:us-central1.my-reservation)
        reservation_pattern = re.compile(r"^[\w-]+:[\w-]+\.[\w-]+$")
        invalid_reservations = [res_id for res_id in creds.rabbit_reservation_ids if not reservation_pattern.match(res_id)]

        if invalid_reservations:
            _logger.warning(
                f"Rabbit optimization disabled: Invalid reservation ID format. "
                f"Expected format: 'admin_project:region.reservation_name'. "
                f"Invalid IDs: {invalid_reservations}. "
                f"Example: 'my-project:us-central1.my-reservation'"
            )
            return connection

        # Get the BigQuery client from the connection
        bq_client = connection.handle

        # Check if already patched to avoid double-patching
        if hasattr(bq_client, cls.RABBIT_PATCHED_MARKER):
            return connection

        # Initialize Rabbit optimizer
        rabbit_optimizer = RabbitBQJobOptimizer(api_key=creds.rabbit_api_key, base_url=creds.rabbit_base_url)

        rabbit_config = {
            "defaultPricingMode": creds.rabbit_default_pricing_mode,
            "reservationIds": creds.rabbit_reservation_ids,
        }

        _logger.info(
            f"Rabbit optimization enabled | Default pricing mode: {creds.rabbit_default_pricing_mode} | " f"Reservations: {creds.rabbit_reservation_ids}"
        )

        # Store original query method
        original_query_method = bq_client.query

        # Create patched query method
        def patched_query(query, *args, job_config=None, **kwargs):
            """
            Intercepted query method with Rabbit optimization.

            This function replaces the BigQuery client's query() method to:
            1. Capture the query string and job configuration
            2. Send configuration to Rabbit API for optimization
            3. Apply optimized configuration (e.g., reservation assignment)
            4. Execute query with optimal pricing

            Args:
                query: SQL query string to execute
                *args: Positional arguments passed to original query method
                job_config: BigQuery QueryJobConfig object
                **kwargs: Keyword arguments passed to original query method

            Returns:
                QueryJob: BigQuery query job object (same as standard behavior)

            Note:
                On optimization failure, falls back to original configuration
                and logs a warning. Query execution always continues.
            """

            # Store original job config for fallback
            original_job_config = job_config
            job_config_to_use = original_job_config
            optimized = False

            # Attempt Rabbit API optimization (use skeleton when no job_config is provided)
            try:
                _logger.info("Optimizing BigQuery job configuration")
                # Build configuration dict from existing job_config or a minimal skeleton
                if job_config:
                    config_dict = job_config.to_api_repr()
                else:
                    # Minimal valid configuration skeleton for BigQuery query jobs
                    config_dict = {
                        "query": {
                            "useLegacySql": False,
                            "priority": "INTERACTIVE",
                            # query string added below
                        }
                    }

                # Ensure SQL query is present in the configuration sent to the optimizer
                if "query" not in config_dict:
                    config_dict["query"] = {}
                config_dict["query"]["query"] = query

                # Optimize via Rabbit API
                optimization_config = OptimizationConfig(type="reservation_assignment", config=rabbit_config)

                # Debug logging: dbt's logging framework handles output filtering
                _logger.debug(f"Original job configuration: {json.dumps(config_dict, indent=2)}")
                _logger.debug(f"Optimization config: {json.dumps(asdict(optimization_config), indent=2)}")

                result = rabbit_optimizer.optimize_job(
                    configuration={"configuration": config_dict},
                    enabledOptimizations=[optimization_config],
                )

                # Debug logging: serialize result for debugging
                result_dict = asdict(result)
                _logger.debug(f"Rabbit API optimization result: {json.dumps(result_dict, indent=2)}")

                # Get optimized configuration
                optimized_config = result.optimizedJob["configuration"]

                # Convert back to QueryJobConfig
                from google.cloud.bigquery import QueryJobConfig

                optimized_job_config = QueryJobConfig.from_api_repr(optimized_config)
                job_config_to_use = optimized_job_config
                optimized = True

                _logger.info("Job config optimized")

            except Exception as e:
                import traceback

                _logger.error(f"Job config optimization failed, falling back to original config: {str(e)}\n{traceback.format_exc()}")

                # Fall back to original job_config (may be None)
                job_config_to_use = original_job_config

            # Execute BigQuery query with optimized (or original/None) configuration
            try:
                query_result = original_query_method(query, *args, job_config=job_config_to_use, **kwargs)
                _logger.info("BigQuery job submitted successfully")
                return query_result

            except Exception as e:
                import traceback

                # If we used optimized config and it failed, try with original
                if optimized:
                    _logger.error(f"BigQuery job execution with optimized config failed: {str(e)}\n{traceback.format_exc()}")
                    _logger.info("Retrying with original configuration")
                    query_result = original_query_method(query, *args, job_config=original_job_config, **kwargs)
                    _logger.info("BigQuery job executed successfully with original config")
                    return query_result
                else:
                    # Already using original config
                    raise

        # Apply the patch
        bq_client.query = patched_query

        # Mark as patched only after successful patch application
        setattr(bq_client, cls.RABBIT_PATCHED_MARKER, True)

        return connection
