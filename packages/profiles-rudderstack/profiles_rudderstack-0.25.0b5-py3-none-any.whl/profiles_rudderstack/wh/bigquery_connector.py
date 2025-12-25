#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bigquery connector."""

import pandas as pd
from logging import getLogger
from google.oauth2 import service_account
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from profiles_rudderstack.wh.connector_base import ConnectorBase, register_connector


@register_connector
class BigqueryConnector(ConnectorBase):
    REF_QUOTES = "`"

    @staticmethod
    def standardize_ref_name(ref_name: str) -> str:
        return ref_name

    @staticmethod
    def get_warehouse_config(config: dict):
        return {
            "credentials": config.get("credentials"),
            "project_id": config.get("project_id"),
            "schema": config.get("schema"),
        }

    def __init__(self, config: dict, **kwargs) -> None:
        self.logger = getLogger("bigquery_connector")
        super().__init__(config, **kwargs)

        self.engine = create_engine(
            "bigquery://", credentials_info=self.creds["credentials"]
        )
        self.bq_credentials = service_account.Credentials.from_service_account_info(
            self.creds["credentials"]
        )
        self.connection = Session(self.engine)
        self.connection.autocommit = True

    def write_to_table(self, df, table_name, schema=None, if_exists="append"):
        # pandas takes care of quoting the relation name so we need to remove the custom quotes from the relation names that we add on WHT side.
        table_name = table_name.replace(self.REF_QUOTES, "")
        if not schema:
            raise Exception("Schema name is required for writing table to BigQuery.")
        schema = schema.replace(self.REF_QUOTES, "")
        project = self.creds["project_id"]
        destination_table_path = f"{project}.{schema}.{table_name}"

        pd.DataFrame.to_gbq(
            df,
            destination_table_path,
            project_id=project,
            if_exists="replace",
            credentials=self.bq_credentials,
        )
