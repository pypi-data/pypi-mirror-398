from pandas import DataFrame
from typing import Any, Optional, Union, Iterator, Tuple
from abc import ABC, abstractmethod
from profiles_rudderstack.go_client import get_gorpc
import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
from profiles_rudderstack.wh.connector_base import ConnectorBase


# Base Interfcae for client
class BaseClient(ABC):
    def __init__(self, wh_type: str, db: str, schema: str, project_id: int, common_props_material_ref: int) -> None:
        self.snowpark_session: Any = None
        self.is_snowpark_enabled: bool = False
        self.wh_connection: Optional[ConnectorBase] = None
        self.wh_type = wh_type
        self.db = db
        self.schema = schema
        self.__gorpc = get_gorpc()
        self.__project_id = project_id
        self.__common_props_material_ref = common_props_material_ref

    def get_connection_and_target(self) -> Tuple[str, str]:
        response = self.__gorpc.GetConnectionAndTarget(
            tunnel.GetConnectionAndTargetRequest(project_id=self.__project_id, material_ref=self.__common_props_material_ref))
        
        return response.connection_name, response.target_name

    def query_sql_without_result(self, sql: str):
        self.__gorpc.QuerySqlWithoutResult(
            tunnel.QuerySqlWithoutResultRequest(project_id=self.__project_id, material_ref=self.__common_props_material_ref, sql=sql))

    def query_template_without_result(self, this, template: str):
        """Query a template without result
        Parameters:
            this (WhtMaterial): The material object
            template (str): The template to query
        """
        material_ref = this._WhtMaterial__material_ref
        self.__gorpc.QueryTemplateWithoutResult(tunnel.QueryTemplateWithoutResultRequest(
            project_id=self.__project_id, material_ref=material_ref, template=template))

    @abstractmethod
    def query_sql_with_result(self, sql: str) -> DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def get_df(self, selector_sql: str, batching: bool, batch_size: int) -> Union[DataFrame, Iterator[DataFrame]]:
        raise NotImplementedError()

    def get_snowpark_df(self, selector_sql: str):
        raise NotImplementedError(
            "get_snowpark_df is only supported for Snowpark enabled Snowflake warehouse, please use get_df for non-Snowpark enabled warehouses")

    @abstractmethod
    def write_df_to_table(self, df, table: str, schema: str = "", append_if_exists: bool = False) -> None:
        raise NotImplementedError()
