#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Databricks Connector."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from logging import Logger
from databricks.sdk.core import Config, oauth_service_principal
from profiles_rudderstack.wh.connector_base import ConnectorBase, register_connector


@register_connector
class DatabricksConnector(ConnectorBase):
    REF_QUOTES = "`"

    @staticmethod
    def standardize_ref_name(ref_name: str) -> str:
        return ref_name.lower()

    @staticmethod
    def get_warehouse_config(config: dict):
        return {
            "user": config.get("user"),
            "host": config.get("host"),
            "port": config.get("port"),
            "http_endpoint": config.get("http_endpoint"),
            "access_token": config.get("access_token"),
            "client_id": config.get("client_id"),
            "client_secret": config.get("client_secret"),
            "catalog": config.get("catalog"),
            "schema": config.get("schema"),
        }

    def __init__(self, config: dict, **kwargs) -> None:
        self.logger = Logger("DatabricksConnector")
        super().__init__(config, **kwargs)

        creds = self.creds
        host = creds.get('host')
        http_endpoint = creds.get('http_endpoint')
        catalog = creds.get('catalog')
        schema = creds.get('schema')

        if not all([host, http_endpoint, catalog, schema]):
            missing_fields = [field for field, value in {
                'host': host,
                'http_endpoint': http_endpoint,
                'catalog': catalog,
                'schema': schema
            }.items() if not value]
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")

        def safe_port_conversion(port_str):
            try:
                if port_str is None:
                    return 443
                return int(float(port_str))
            except (ValueError, TypeError):
                raise ValueError(f"Could not convert port '{port_str}' to integer")
        port = safe_port_conversion(creds.get('port', 443))

        access_token = creds.get('access_token')
        client_id = creds.get('client_id')
        client_secret = creds.get('client_secret')

        if access_token:
            connection_string = (
                f"databricks://token:{access_token}@{host}"
                f"?http_path={http_endpoint}&catalog={catalog}&schema={schema}"
            )
            self.engine = create_engine(connection_string)

        elif client_id and client_secret:
            def credential_provider():
                cfg = Config(
                    host=f"https://{host}",
                    client_id=client_id,
                    client_secret=client_secret,
                )
                return oauth_service_principal(cfg)

            self.engine = create_engine(
                f"databricks+connector://@{host}:{port}/default",
                connect_args={
                    "http_path": http_endpoint,
                    "catalog": catalog,
                    "schema": schema,
                    "credentials_provider": credential_provider,
                },
            )
        else:
            raise ValueError("No valid credentials found. Either access_token or client_id and client_secret must be provided.")
        self.connection = Session(self.engine)
        self.connection.autocommit = True

    def write_to_table(self, df, table_name, schema, if_exists):
        # not the best method to achieve this (performance wise)
        df.to_sql(name=table_name, con=self.engine,
                  schema=schema, index=False, if_exists=if_exists)
