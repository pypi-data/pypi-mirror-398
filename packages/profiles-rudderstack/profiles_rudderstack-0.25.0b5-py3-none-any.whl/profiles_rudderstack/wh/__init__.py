#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module for handling various warehouse connections"""

from typing import Union

from profiles_rudderstack.wh.connector_base import connector_classes, ConnectorBase
from profiles_rudderstack.wh.redshift_pb_connector import RedShiftConnector
from profiles_rudderstack.wh.snowflake_connector import SnowflakeConnector
from profiles_rudderstack.wh.databricks_connector import DatabricksConnector
from profiles_rudderstack.wh.bigquery_connector import BigqueryConnector
from profiles_rudderstack.wh.pg_connector import PostgresConnector

# SnowflakeConnector not used currently in profiles_rudderstack


def ProfilesConnector(config: dict, **kwargs) -> ConnectorBase:
    """Creates a connector object based on the config provided

    Args:
        config: A dictionary containing the credentials and database information for the connector.
        **kwargs: Additional keyword arguments to pass to the connector.

    Returns:
        ConnectorBase: Connector object.

    Raises:
        Exception: Connector not found
    """

    warehouse_type = config.get("type").lower()
    connector = connector_classes.get(warehouse_type, None)
    if connector is None:
        raise Exception(f"Connector {warehouse_type} not found")

    connector = connector(config, **kwargs)
    return connector
