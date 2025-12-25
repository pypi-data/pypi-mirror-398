import datetime
from google.protobuf import json_format
from typing import Optional, Tuple, Dict, Any
from profiles_rudderstack.go_client import get_gorpc
import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
from profiles_rudderstack.client import WhClient


class WhtContext:
    def __init__(self, project_id: int, common_props_material_ref: int):
        self.__project_id = project_id
        # Warning: the common_props_material_ref should not be used to refer to a material only to access fields common to all materials
        self.__common_props_material_ref = common_props_material_ref
        self.__gorpc = get_gorpc()
        self.is_null_ctx = self.__is_null_context()
        if not self.is_null_ctx:
            self.client = WhClient(project_id, common_props_material_ref)
            self.snowpark_session = self.client.snowpark_session

    def __is_null_context(self) -> bool:
        null_ctx_res: tunnel.IsNullContextResponse = self.__gorpc.IsNullContext(
            tunnel.IsNullContextRequest(project_id=self.__project_id, material_ref=self.__common_props_material_ref))
        return null_ctx_res.is_null_ctx

    def time_info(self) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
        time_info_res: tunnel.GetTimeInfoResponse = self.__gorpc.GetTimeInfo(
            tunnel.GetTimeInfoRequest(project_id=self.__project_id, material_ref=self.__common_props_material_ref,))

        begin_time = time_info_res.begin_time.ToDatetime(
        ) if time_info_res.begin_time is not None else None

        end_time = time_info_res.end_time.ToDatetime(
        ) if time_info_res.end_time is not None else None

        return begin_time, end_time

    def site_config(self) -> Dict[str, Any]:
        site_config_res: tunnel.GetSiteConfigResponse = self.__gorpc.GetSiteConfig(
            tunnel.GetSiteConfigRequest(project_id=self.__project_id, material_ref=self.__common_props_material_ref))

        return json_format.MessageToDict(site_config_res.site_config)


class WhtContextStore:
    def __init__(self):
        self.store:  Dict[int, WhtContext] = {}

    def get_context(self, project_id: int, material_ref: int) -> WhtContext:
        if project_id not in self.store:
            wht_ctx = WhtContext(project_id, material_ref)
            if wht_ctx.is_null_ctx:
                return wht_ctx

            self.store[project_id] = wht_ctx

        return self.store[project_id]

    def remove_context(self, project_id: int):
        if project_id in self.store:
            del self.store[project_id]
