from profiles_rudderstack.client.client_base import BaseClient
from typing import Dict, Any
import importlib
import pandas as pd


def remap_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Remaps credentials from profiles siteconfig to the expected format from snowflake session

    Args:
        credentials (dict): Data warehouse credentials from profiles siteconfig

    Returns:
        dict: Data warehouse creadentials remapped in format that is required to create a snowpark session
    """
    new_creds = {k if k != 'dbname' else 'database': v for k,
                 v in credentials.items() if k != 'type'}

    return new_creds


class SnowparkClient(BaseClient):
    def __init__(self, creds: Dict[str, Any], db: str, wh_type: str, schema: str, project_id: int, common_props_material_ref: int):
        super().__init__(wh_type, db, schema, project_id, common_props_material_ref)
        snowpark_creds = remap_credentials(creds)
        Session = importlib.import_module('snowflake.snowpark.session').Session
        # default to True
        snowpark_creds['client_session_keep_alive'] = snowpark_creds.get(
            'keepSessionAlive', True)
        self.snowpark_session = Session.builder.configs(
            snowpark_creds).create()
        self.is_snowpark_enabled = True

    def query_sql_with_result(self, sql: str):
        rows = self.snowpark_session.sql(sql).collect()
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame([row.as_dict() for row in rows])
        return df

    def get_df(self, selector_sql: str, batching, batch_size):
        # Snowpark does not support declaring batch size
        if batching:
            return self.snowpark_session.sql(selector_sql).to_pandas_batches()

        return self.snowpark_session.sql(selector_sql).to_pandas()

    def get_snowpark_df(self, selector_sql: str):
        return self.snowpark_session.sql(selector_sql)

    def write_df_to_table(self, df, table: str, schema="", append_if_exists: bool = False) -> None:
        table_name = table
        schema = self.schema if schema == "" else schema
        df.columns = df.columns.str.upper()

        self.snowpark_session.write_pandas(
            df, table_name=table_name, schema=schema, auto_create_table=True, overwrite=False if append_if_exists else True)
