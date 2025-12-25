#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazon RedShift Connector."""

import urllib.parse
import pandas as pd
import pandas_redshift as pr

from sqlalchemy import create_engine
from sqlalchemy import orm as sa_orm

import redshift_connector

from logging import Logger
from profiles_rudderstack.wh.connector_base import ConnectorBase, register_connector


class BatchIterator:
    def __init__(self, query: str, batch_size: int, connection):
        self.batch_size = batch_size
        self.connection = connection
        self.cursor = self.connection.cursor()
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
class RedShiftConnector(ConnectorBase):
    REF_QUOTES = '"'

    @staticmethod
    def standardize_ref_name(ref_name: str) -> str:
        return ref_name.lower()

    @staticmethod
    def get_warehouse_config(config: dict):
        return {
            "host": config.get("host"),
            "port": config.get("port"),
            "user": config.get("user"),
            "password": config.get("password"),
            "database": config.get("dbname"),
            "schema": config.get("schema"),
        }

    def __init__(self, config: dict, **kwargs) -> None:
        self.logger = Logger("RedShiftConnector")
        super().__init__(config, **kwargs)

        creds = self.creds
        self.s3_config = kwargs.get("s3_config", None)
        encoded_password = urllib.parse.quote(creds["password"], safe="")
        connection_string = f"postgresql://{creds['user']}:{encoded_password}@{creds['host']}:{creds['port']}/{creds['database']}"
        self.engine = create_engine(connection_string)

        Session = sa_orm.sessionmaker()
        Session.configure(bind=self.engine)
        self.connection = Session()
        self.connection.autocommit = True

        # Set search path if schema is provided
        if creds.get("schema", None):
            self.connection.execute(f"SET search_path TO {creds['schema']}")

    def get_table_data_batches(self, query: str, batch_size):
        conn = redshift_connector.connect(
            self.creds["user"], self.creds["database"], self.creds["password"], self.creds["port"], self.creds["host"])
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {self.creds['schema']}")
        cursor.close()
        return BatchIterator(query, batch_size, conn)

    def write_to_table(self, df, table_name, schema=None, if_exists="append"):
        if self.s3_config is None:
            df.to_sql(name=table_name, con=self.engine,
                      schema=schema, index=False, if_exists=if_exists)
        else:
            pr.connect_to_redshift(
                dbname=self.creds["database"],
                host=self.creds["host"],
                port=self.creds["port"],
                user=self.creds["user"],
                password=self.creds["password"],
            )

            s3_bucket = self.s3_config.get("bucket", None)
            s3_sub_dir = self.s3_config.get("path", None)

            pr.connect_to_s3(
                aws_access_key_id=self.s3_config["access_key_id"],
                aws_secret_access_key=self.s3_config["access_key_secret"],
                bucket=s3_bucket,
                subdirectory=s3_sub_dir
                # As of release 1.1.1 you are able to specify an aws_session_token (if necessary):
                # aws_session_token = <aws_session_token>
            )

            # Write the DataFrame to S3 and then to redshift
            pr.pandas_to_redshift(
                data_frame=df,
                redshift_table_name=f"{schema}.{table_name}",
                append=if_exists == "append",
            )
