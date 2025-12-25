#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostgreSQL Connector."""

import urllib.parse
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy import orm as sa_orm

import psycopg2

from logging import Logger
from typing import Iterator
from profiles_rudderstack.wh.connector_base import ConnectorBase, register_connector

class BatchIterator:
    def __init__(self, query: str, batch_size: int, connection):
        self.batch_size = batch_size
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.cursor.execute(query)
        self.column_names = [desc[0] for desc in self.cursor.description]

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
class PostgresConnector:
    @staticmethod
    def standardize_ref_name(ref_name: str) -> str:
        return ref_name.lower()

    @staticmethod
    def get_warehouse_config(config: dict):
        return {
            "host": config.get("host"),
            "port": int(config.get("port")),
            "user": config.get("user"),
            "password": config.get("password"),
            "database": config.get("dbname"),
            "schema": config.get("schema"),
        }

    def __init__(self, config: dict, **kwargs) -> None:
        self.logger = Logger("PostgresConnector")
        self.creds = self.get_warehouse_config(config)

        encoded_password = urllib.parse.quote(self.creds["password"], safe="")
        connection_string = f"postgresql://{self.creds['user']}:{encoded_password}@{self.creds['host']}:{self.creds['port']}/{self.creds['database']}"
        self.engine = create_engine(connection_string)

        Session = sa_orm.sessionmaker()
        Session.configure(bind=self.engine)
        self.connection = Session()
        self.connection.autocommit = True

        # Set search path if schema is provided
        if self.creds.get("schema"):
            self.connection.execute(f"SET search_path TO {self.creds['schema']}")

    def get_table_data_batches(self, query: str, batch_size: int) -> Iterator[pd.DataFrame]:
        conn = psycopg2.connect(
            dbname=self.creds["database"],
            user=self.creds["user"],
            password=self.creds["password"],
            host=self.creds["host"],
            port=self.creds["port"]
        )

        if self.creds.get("schema"):
            cursor = conn.cursor()
            cursor.execute(f"SET search_path TO {self.creds['schema']}")
            cursor.close()

        return BatchIterator(query, batch_size, conn)

    def write_to_table(self, df, table_name, schema=None, if_exists="append"):
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=schema,
            index=False,
            if_exists=if_exists
        )

    def close(self) -> None:
        """Close all database connections."""
        self.connection.close()
        self.engine.dispose()