from profiles_rudderstack.client.client_base import BaseClient
from profiles_rudderstack.logger import Logger
from typing import Dict, Any
from profiles_rudderstack.wh import ProfilesConnector
from profiles_rudderstack.wh.connector_base import ConnectorBase


class WarehouseClient(BaseClient):
    def __init__(self, creds: Dict[str, Any], db: str, wh_type: str, schema: str, project_id: int, common_props_material_ref: int):
        super().__init__(wh_type, db, schema, project_id, common_props_material_ref)
        self.logger = Logger("WarehouseClient")
        s3_config = creds.get("s3", None)

        if wh_type == "redshift":
            if s3_config is None:
                self.logger.warn("its recommended to provide s3 config in siteconfig to get added performance benefit in redshift (https://stackoverflow.com/questions/38402995/how-to-write-data-to-redshift-that-is-a-result-of-a-dataframe-created-in-python)")

            creds.update({"port": int(creds.get("port", 0))})

        self.wh_connection: ConnectorBase = ProfilesConnector(
            creds, s3_config=s3_config)

    def query_sql_with_result(self, sql: str):
        return self.wh_connection.run_query(sql)

    def get_df(self, selector_sql: str, batching: bool, batch_size: int):
        if batching:
            return self.wh_connection.get_table_data_batches(selector_sql, batch_size=batch_size)

        return self.wh_connection.run_query(selector_sql)

    def write_df_to_table(self, df, table: str, schema="", append_if_exists: bool = False) -> None:
        table_name = table
        schema = self.schema if schema == "" else schema
        df.columns = df.columns.str.upper()
        self.wh_connection.write_to_table(
            df, table_name, schema, if_exists="append" if append_if_exists else "replace")
