import inspect
from google.protobuf import struct_pb2, json_format
import json
from typing import Type, cast
from types import FrameType
from profiles_rudderstack.tunnel.tunnel_pb2_grpc import WhtServiceStub
from profiles_rudderstack.model import BaseModelType
from profiles_rudderstack.material import WhtFolder
from profiles_rudderstack.utils import RefManager
from profiles_rudderstack.logger import Logger
import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel


class WhtProject:
    def __init__(self, project_id: int, base_proj_ref: int, current_supported_schema_version: int, pb_version: str, ref_manager: RefManager, gorpc: WhtServiceStub):
        self.__proj_id = project_id
        self.__base_proj_ref = base_proj_ref
        self.__gorpc = gorpc
        self.__ref_manager = ref_manager
        self.current_supported_schema_version = current_supported_schema_version
        self.pb_version = pb_version
        self.logger = Logger("WhtProject")

    # Passing extra arguments to the constructor of a model which does not support it will result in an error
    # So we need to check if the model supports it or not
    def __supports_model_name_arg(self, model_class: Type[BaseModelType]):
        init_signature = inspect.signature(model_class.__init__)
        params = init_signature.parameters
        # model_name is supposed to be the 6th argument (including self)
        return len(params) > 5

    def __create_factory_func(self, model_class: Type[BaseModelType], model_type: str):
        def factory(base_proj_ref: int, model_name: str, build_spec: dict, parent_folder: WhtFolder):
            if self.__supports_model_name_arg(model_class):
                model = model_class(build_spec, self.current_supported_schema_version, self.pb_version, parent_folder, model_name)
            else:
                model = model_class(build_spec, self.current_supported_schema_version, self.pb_version)
            materialization = struct_pb2.Struct()
            mzn = model.materialization
            if mzn is not None:
                json_format.ParseDict(mzn._asdict(), materialization)

            ids = []
            id_struct = struct_pb2.Struct()
            model_ids = model.ids
            if model_ids is not None:
                for id in model_ids:
                    json_format.ParseDict(id._asdict(), id_struct)
                    ids.append(id_struct)

            contract = None
            if model.contract is not None:
                if isinstance(model.contract, str):
                    contract = model.contract
                else:
                    contract = json.dumps(model.contract)

            features = []
            if model.features is not None:
                for feature in model.features:
                    feature_struct = struct_pb2.Struct()
                    json_format.ParseDict(feature._asdict(), feature_struct)
                    features.append(feature_struct)

            new_py_model_res: tunnel.NewPythonModelResponse = self.__gorpc.NewPythonModel(tunnel.NewPythonModelRequest(
                project_id=self.__proj_id,
                name=model_name,
                display_name=model.display_name,
                model_type=model_type,
                build_spec=json.dumps(build_spec),
                base_proj_ref=base_proj_ref,
                parent_folder_ref=parent_folder._WhtFolder__folder_ref,
                entity_key=model.entity_key,
                cohort_path=model.cohort_path,
                contract=contract,
                materialization=materialization,
                ids=ids,
                features=features,
            ))

            wht_model_ref = new_py_model_res.model_ref
            py_model_ref = self.__ref_manager.create_ref(self.__proj_id, model)
            contract = model.contract
            finish_pending_ref = new_py_model_res.finish_pending_ref
            return wht_model_ref, py_model_ref, finish_pending_ref

        return factory

    def register_model_type(self, modelClass: Type[BaseModelType]):
        package_name = ""
        # Get the package name from caller, from RegisterExtensions
        frame_type = cast(FrameType,
                          cast(FrameType, inspect.currentframe()).f_back)
        package_info = inspect.getmodule(frame_type)
        if package_info:
            mod = package_info.__name__.split('.')
            package_name = mod[0]
            self.logger.debug(
                f"registering {modelClass.TypeName} from {package_name}")

        model_type = modelClass.TypeName
        schema = struct_pb2.Struct()
        json_format.ParseDict(modelClass.BuildSpecSchema, schema)

        self.__gorpc.RegisterModelType(tunnel.RegisterModelTypeRequest(
            project_id=self.__proj_id,
            model_type=model_type,
            build_spec_schema=schema,
            base_proj_ref=self.__base_proj_ref,
        ))

        factory = self.__create_factory_func(modelClass, model_type)
        self.__ref_manager.create_ref_with_key(self.__proj_id, model_type,
                                               {"factory_func": factory, "package": package_name, "model_class": modelClass})
