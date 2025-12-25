#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SnowFlake connector."""

import pandas as pd
import urllib.parse
from logging import getLogger
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from snowflake.sqlalchemy import URL

from snowflake.connector.pandas_tools import write_pandas
from snowflake.connector import connect

from profiles_rudderstack.wh.connector_base import ConnectorBase, register_connector


class BatchIterator:
    def __init__(self, query: str, batch_size: int, connection):
        self.batch_size = batch_size
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.cursor.execute("ALTER SESSION SET CLIENT_PREFETCH_THREADS=8")
        self.cursor.execute(query)
        self.column_names = [col[0] for col in self.cursor.description]

    def __iter__(self):
        return self

    def __next__(self):
        rows = self.cursor.fetchmany(self.batch_size)
        if not rows:
            self.cursor.close()
            self.connection.close()
            raise StopIteration
        return pd.DataFrame(rows, columns=self.column_names)


@register_connector
class SnowflakeConnector(ConnectorBase):
    REF_QUOTES = '"'

    @staticmethod
    def standardize_ref_name(ref_name: str) -> str:
        return ref_name.upper()

    @staticmethod
    def get_warehouse_config(config: dict):
        return {
            "user": config.get("user"),
            "password": config.get("password"),
            "account": config.get("account"),
            "warehouse": config.get("warehouse"),
            "role": config.get("role"),
            "database": config.get("dbname"),
            "schema": config.get("schema"),
            # defaults to True
            "keepSessionAlive": config.get("keepSessionAlive", True),
            "useKeyPairAuth": config.get("useKeyPairAuth"),
            "privateKey": config.get("privateKey"),
            "privateKeyPassphrase": config.get("privateKeyPassphrase"),
        }

    def __init__(self, config: dict, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.logger = getLogger("snowflake_connector")

        creds = self.creds
        if creds.get("useKeyPairAuth", False):
            private_key = creds["privateKey"]
            passphrase = creds.get("privateKeyPassphrase", None)
            p_key = serialization.load_pem_private_key(
                        private_key.encode(), 
                        password=(
                            passphrase.encode() 
                            if passphrase 
                            else None
                        ),
                        backend=default_backend()
                    )
            self.engine = create_engine(
                URL(account=creds['account'], user=creds['user'], database=creds['database'], schema=creds['schema'], warehouse=creds['warehouse'], role=creds['role'], client_session_keep_alive=creds['keepSessionAlive']), connect_args={'private_key': p_key}
            )
        else:
            encoded_password = urllib.parse.quote(creds["password"], safe="")
            connection_string = f"snowflake://{creds['user']}:{encoded_password}@{creds['account']}/{creds['database']}/{creds['schema']}?warehouse={creds['warehouse']}&role={creds['role']}&client_session_keep_alive={creds['keepSessionAlive']}"
            self.engine = create_engine(connection_string)
        self.connection = Session(self.engine)
        self.connection.autocommit = True

    def get_table_data_batches(self, query: str, batch_size):
        conn = self.__create_connection()
        return BatchIterator(query, batch_size, conn)

    # We are using the snowflake.connector to write and read only batched data from Snowflake
    # The sqlalchemy engine in the constructor is used for reading data, so we have a separate method for snowflake.connector connection
    # TODO: remove sqlalchemy engine and use snowflake.connector for reading data as well
    def __create_connection(self):
        connection_params = self.creds
        connection_params["client_session_keep_alive"] = connection_params["keepSessionAlive"]
        
        if connection_params.get("useKeyPairAuth", False):
            private_key = connection_params["privateKey"]
            passphrase = connection_params.get("privateKeyPassphrase", None)
            p_key = serialization.load_pem_private_key(
                private_key.encode(),
                password=(
                    passphrase.encode()
                    if passphrase
                    else None
                ),
                backend=default_backend()
            )
            connection_params["private_key"] = p_key
            
        return connect(**connection_params)

    def write_to_table(self, df, table_name, schema=None, if_exists="append"):
        write_conn = self.__create_connection()
        write_pandas(write_conn, df, table_name, schema=schema,
                     quote_identifiers=False, overwrite=if_exists == "replace", auto_create_table=True)
