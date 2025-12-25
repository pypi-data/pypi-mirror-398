import json
from os import path
from typing import Literal, Optional, List, Dict, Any, Union
from google.protobuf import struct_pb2, json_format
import pandas as pd
from profiles_rudderstack.go_client import get_gorpc
from profiles_rudderstack.logger import Logger
import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
from profiles_rudderstack.wht_context import WhtContextStore


class Contract:
    def __init__(self, contract_ref: int) -> None:
        self.__contract_ref = contract_ref

    def ref(self) -> int:
        return self.__contract_ref
    
class WhtId:
    def __init__(self, id: Dict):
        self.id = id

    def select(self) -> str:
        return self.id["select"]
    
    def entity(self) -> str:
        return self.id["entity"]
    
    def type(self) -> str:
        return self.id["type"]

class WhtModel:
    def __init__(self, project_id: int, material_ref: int):
        self.__project_id = project_id
        self.__material_ref = material_ref
        self.__gorpc = get_gorpc()
        self.logger = Logger("WhtModel")

    def name(self) -> str:
        """Get the name of the model

        Returns:
            str: Name of the model
        """
        nameResponse: tunnel.ModelNameResponse = self.__gorpc.ModelName(
            tunnel.NameRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return nameResponse.model_name
    
    def model_type(self) -> str:
        response: tunnel.ModelTypeResponse = self.__gorpc.ModelType(
            tunnel.ModelTypeRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        return response.model_type

    def db_object_name_prefix(self) -> str:
        """Get the db object name prefix of the model

        Returns:
            str: db object name prefix of the model
        """
        dbObjectNamePrefixResponse: tunnel.DbObjectNamePrefixResponse = self.__gorpc.DbObjectNamePrefix(
            tunnel.DbObjectNamePrefixRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return dbObjectNamePrefixResponse.db_object_name_prefix
    
    def model_ref(self) -> str:
        response: tunnel.ModelReferenceResponse = self.__gorpc.ModelReference(
            tunnel.ModelReferenceRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return response.model_ref
    
    def model_ref_from_level_root(self) -> str:
        response: tunnel.ModelReferenceResponse = self.__gorpc.ModelReferenceFromLevelRoot(
            tunnel.ModelReferenceRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return response.model_ref
    
    def ids(self) -> List[WhtId]:
        response: tunnel.ModelIdsResponse = self.__gorpc.ModelIds(
            tunnel.ModelIdsRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        
        ids = []
        for id in response.ids:
            dict_id = json_format.MessageToDict(id)
            ids.append(WhtId(dict_id))
        return ids
    
    def build_spec(self) -> dict:
        response: tunnel.ModelBuildSpecResponse = self.__gorpc.ModelBuildSpec(
            tunnel.ModelBuildSpecRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return json_format.MessageToDict(response.build_spec)
    
    def hash(self) -> str:
        response: tunnel.ModelHashResponse = self.__gorpc.ModelHash(
            tunnel.ModelHashRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return response.hash

    def materialization(self) -> dict:
        """Get the materialization of the model

        Returns:
            str: Materialization of the model
        """
        mznResponse: tunnel.MaterializationResponse = self.__gorpc.Materialization(
            tunnel.MaterializationRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        return json_format.MessageToDict(mznResponse.materialization)

    def encapsulating_model(self):
        """
        Get the encapsulating model of the model

        Returns:
            WhtModel: encapsulating model
        """
        encapsulatingMaterialResponse: tunnel.EncapsulatingMaterialResponse = self.__gorpc.EncapsulatingMaterial(
            tunnel.EncapsulatingMaterialRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return WhtModel(self.__project_id, encapsulatingMaterialResponse.encapsulating_material_ref)

    def entity(self) -> Optional[Dict]:
        """
        Get the entity of the model

        Returns:
            Dict: Entity of the model
        """
        entityResponse: tunnel.EntityResponse = self.__gorpc.Entity(
            tunnel.EntityRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        entity = json_format.MessageToDict(entityResponse.entity)
        if len(entity) == 0:  # empty dict
            return None

        return entity

    def get_description(self) -> Optional[str]:
        descriptionResponse: tunnel.GetVarDescriptionResponse = self.__gorpc.GetVarDescription(
            tunnel.GetVarDescriptionRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return descriptionResponse.description
    
    def time_filtering_column(self) -> str:
        response: tunnel.GetTimeFilteringColumnResponse = self.__gorpc.GetTimeFilteringColumn(
            tunnel.GetTimeFilteringColumnRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        return response.column_name

class BaseWhtProject:
    def __init__(self, project_id: int, material_ref: int) -> None:
        self.__gorpc = get_gorpc()
        self.__material_ref = material_ref
        self.__project_id = project_id

    def project_path(self) -> str:
        """Get the project path

        Returns:
            str: project folder
        """
        project_path_res: tunnel.GetProjectPathResponse = self.__gorpc.GetProjectPath(
            tunnel.GetProjectPathRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return project_path_res.project_path
    
    def warehouse_credentials(self) -> Dict[str, Any]:
        response: tunnel.GetWarehouseCredentialsResponse = self.__gorpc.GetWarehouseCredentials(
            tunnel.GetWarehouseCredentialsRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        creds = json_format.MessageToDict(response.credentials) 
        if creds["type"] == "redshift":
            creds.update({"port": int(creds.get("port", 0))})

        return creds

    def is_rudder_backend(self) -> bool:
        is_rudder_backend_res: tunnel.GetIsRudderBackendResponse = self.__gorpc.GetIsRudderBackend(
            tunnel.GetIsRudderBackendRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return is_rudder_backend_res.is_rudder_backend

    def entities(self) -> Dict[str, Any]:
        """Get the entities of the project

        Returns:
            Dict: Entities of the project
        """
        entities_res: tunnel.GetEntitiesResponse = self.__gorpc.GetEntities(
            tunnel.GetEntitiesRequest(project_id=self.__project_id, material_ref=self.__material_ref))
        entities = {}
        for key, entity in entities_res.entities.items():
            entities[key] = json_format.MessageToDict(entity)

        return entities
    
    def models(self, **kwargs) -> List[WhtModel]:
        response: tunnel.GetAllMaterialsResponse = self.__gorpc.GetAllMaterials(
            tunnel.GetAllMaterialsRequest(project_id=self.__project_id, material_ref=self.__material_ref, **kwargs))
        models = []
        for material_ref in response.material_refs:
            models.append(WhtModel(self.__project_id, material_ref))
        return models
        
    
class WhtFolder:
    def __init__(self, project_id: int, folder_ref: int):
        self.__project_id = project_id
        self.__folder_ref = folder_ref
        self.__gorpc = get_gorpc()

    def add_child_specs(self, model_name: str, model_type: str, build_spec: dict) -> None:
        build_spec_struct = struct_pb2.Struct()
        json_format.ParseDict(build_spec, build_spec_struct)
        self.__gorpc.AddChildSpecs(tunnel.AddChildSpecsRequest(
            project_id=self.__project_id,
            folder_ref=self.__folder_ref,
            model_name=model_name,
            model_type=model_type,
            build_spec=build_spec_struct
        ))

    def folder_ref(self) -> str:
        response: tunnel.FolderReferenceResponse = self.__gorpc.FolderReference(
            tunnel.FolderReferenceRequest(project_id=self.__project_id, folder_ref=self.__folder_ref))
        return response.folder_ref
    
    def folder_ref_from_level_root(self) -> str:
        response: tunnel.FolderReferenceResponse = self.__gorpc.FolderReferenceFromLevelRoot(
            tunnel.FolderReferenceRequest(project_id=self.__project_id, folder_ref=self.__folder_ref))
        return response.folder_ref


class WhtMaterial:
    _wht_ctx_store = WhtContextStore()

    def __init__(self, project_id: int, material_ref: int, output_folder_suffix: Literal["compile", "run"], default_baseline_name: str = ""):
        self.__project_id = project_id
        self.__material_ref = material_ref
        self.__gorpc = get_gorpc()
        self.__output_folder_suffix: Literal['compile', 'run'] = output_folder_suffix
        self.default_baseline_name = default_baseline_name
        self.model = WhtModel(project_id, material_ref)
        self.base_wht_project = BaseWhtProject(project_id, material_ref)

        self.wht_ctx = self._wht_ctx_store.get_context(
            project_id, material_ref)

        self.logger = Logger("WhtMaterial")

    def string(self) -> str:
        """Get the standardized table name of the material. It should return a string that can be used in SQL."""
        string_res: tunnel.MaterialStringResponse = self.__gorpc.MaterialString(
            tunnel.MaterialStringRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return string_res.material_string

    def name(self) -> str:
        """Get the name of the material

        Returns:
            str: Name of the material
        """
        name_res: tunnel.NameResponse = self.__gorpc.Name(
            tunnel.NameRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return name_res.material_name

    def get_output_folder(self) -> str:
        """Get the output folder path of the material

        Returns:
            str: Output folder of the material
        """
        output_folder_res: tunnel.OutputFolderResponse = self.__gorpc.OutputFolder(
            tunnel.OutputFolderRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return path.join(output_folder_res.output_folder, self.__output_folder_suffix)

    def build_contract(self, contract: Union[str, Dict[Any, Any]]) -> Contract:
        """Builds a contract from a string or a dict

        Args:
            contract (str): The contract to be built

        Returns:
            Contract: The built contract
        """
        if isinstance(contract, dict):
            contract = json.dumps(contract)

        contract_res: tunnel.BuildContractResponse = self.__gorpc.BuildContract(
            tunnel.BuildContractRequest(contract=contract, project_id=self.__project_id))
        return Contract(contract_res.contract_ref)

    def de_ref(self, model_path: Optional[str] = None, **kwargs):
        """Dereference a material

        Args:
            model_path (str): Path to the model

        Keyword Args:
            dependency (str): normal, coercive or optional
            contract (Contract): Contract to be used
            pre_existing (bool): if true we search for pre-existing materials from material registry
            allow_incomplete_materials (bool): materials with complete status as complete(2) as well as incomplete(3)
            remember_context_as (str): saves the context of past/previous material in material registry entry of this material
            time_grain_spec (str): time grain spec

        Returns:
            WhtMaterial: Dereferenced material
        """
        contract = kwargs.get("contract", None)
        contract_ref = contract.ref() if contract is not None else None
        if contract_ref is not None:
            kwargs["contract_ref"] = contract_ref
            kwargs.pop("contract")

        # Auto-inject default baseline name as checkpoint_name for pre_existing DeRefs
        # This provides a sensible default but recipes can override by explicitly passing checkpoint_name
        # Only applies when pre_existing=True since that's when checkpoint_name is required
        if kwargs.get("pre_existing", False) and "checkpoint_name" not in kwargs:
            if self.default_baseline_name:
                kwargs["checkpoint_name"] = self.default_baseline_name

        kwargs_struct = struct_pb2.Struct()
        json_format.ParseDict(kwargs, kwargs_struct)
        de_ref_res: tunnel.DeRefResponse = self.__gorpc.DeRef(tunnel.DeRefRequest(
            project_id=self.__project_id,
            material_ref=self.__material_ref,
            model_path=model_path,
            kwargs=kwargs_struct
        ))
        if de_ref_res.is_null:
            return None

        return WhtMaterial(
            self.__project_id,
            de_ref_res.material_ref,
            self.__output_folder_suffix,
            de_ref_res.default_baseline_name
        )

    def get_columns(self):
        """Get the columns of the material

        Returns:
            List[dict]: List of columns
        """
        get_columns_res: tunnel.GetColumnsResponse = self.__gorpc.GetColumns(
            tunnel.GetColumnsRequest(project_id=self.__project_id, material_ref=self.__material_ref))

        return [{"name": col.name, "type": col.type} for col in get_columns_res.columns]

    def get_df(self, select_columns: Optional[List[str]] = None, batching=False, batch_size=100000):
        """Get the table data of the material.

        Args:
            select_columns (List[str], optional): List of columns to be selected. Defaults to None.
            batching (bool, optional): Whether to use batching. Defaults to False.
            batch_size (int, optional): Batch size(not supported for snowpark). Defaults to 100000.

        Returns:
            DataFrame: Table data as DataFrame or Iterable[DataFrame]
        """
        get_selector_sql = self.__gorpc.GetSelectorSql(tunnel.GetSelectorSqlRequest(
            project_id=self.__project_id, material_ref=self.__material_ref, columns=select_columns))

        return self.wht_ctx.client.get_df(get_selector_sql.sql, batching, batch_size)
    
    def get_selector_sql(self) -> str:
        get_selector_sql: tunnel.GetSelectorSqlResponse = self.__gorpc.GetSelectorSql(tunnel.GetSelectorSqlRequest(
            project_id=self.__project_id, material_ref=self.__material_ref))

        return get_selector_sql.sql

    def get_snowpark_df(self, select_columns: Optional[List[str]] = None):
        """Get the table data of the material as Snowpark DataFrame.

        Args:
            select_columns (List[str], optional): List of columns to be selected. Defaults to None.

        Returns:
            DataFrame: Table data as Snowpark DataFrame
        """
        get_selector_sql = self.__gorpc.GetSelectorSql(tunnel.GetSelectorSqlRequest(
            project_id=self.__project_id, material_ref=self.__material_ref, columns=select_columns))

        return self.wht_ctx.client.get_snowpark_df(get_selector_sql.sql)

    def write_output(self, df: pd.DataFrame, append_if_exists: bool = False):
        """Write the dataframe as the output of the material

        Args:
            df (pd.DataFrame): DataFrame to be written
            append_if_exists (bool, optional): Append to the table if it exists. Defaults to False.
        """
        table_name = self.string()  # standardized table name
        schema = ""

        # todo: need to make it better by using INmaedWhObject interface methods
        def remove_quotes(s):
            return s.replace('`', '').replace('"', '').replace("'", '')
        if "." in table_name:
            parts = table_name.split(".")
            table_name, schema = remove_quotes(parts[-1]), remove_quotes(parts[-2])

        self.wht_ctx.client.write_df_to_table(
            df, table_name, schema, append_if_exists)

    def execute_text_template(self, template: str, skip_material_wrapper=False) -> str:
        template_res: tunnel.ExecuteTextTemplateResponse = self.__gorpc.ExecuteTextTemplate(
            tunnel.ExecuteTextTemplateRequest(project_id=self.__project_id,  material_ref=self.__material_ref, template=template, skip_material_wrapper=skip_material_wrapper))

        return template_res.result
