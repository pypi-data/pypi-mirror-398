import importlib.metadata
import importlib.util
import json
import re
import traceback
from importlib.metadata import version, PackageNotFoundError
from typing import Callable, List, Optional

import grpc
import pkg_resources
import profiles_rudderstack.tunnel.tunnel_pb2 as tunnel
import yaml
from packaging.requirements import Requirement
from profiles_rudderstack.logger import Logger
from profiles_rudderstack.material import WhtMaterial, WhtFolder
from profiles_rudderstack.model import BaseModelType
from profiles_rudderstack.project import WhtProject
from profiles_rudderstack.recipe import PyNativeRecipe
from profiles_rudderstack.tunnel.tunnel_pb2_grpc import PythonServiceServicer, WhtServiceStub
from profiles_rudderstack.utils import RefManager
from profiles_rudderstack.utils import is_valid_package_name
from google.protobuf import json_format
from google.protobuf import struct_pb2

PYTHON_DISTRIBUTION = "profiles-rudderstack"



class PythonRpcService(PythonServiceServicer):
    def __init__(self, go_rpc: WhtServiceStub, current_supported_schema_version: int, pb_version: str):
        self.logger = Logger("PythonRpcService")
        self.ref_manager = RefManager()
        self.current_supported_schema_version = current_supported_schema_version
        self.pb_version = pb_version
        self.gorpc = go_rpc


    def _is_safe_module_name(self, module_name: str) -> bool:
        """
        Validate that the module name contains only safe characters to prevent code injection.
        Only allows alphanumeric characters, underscores, hyphens, and dots.
        """
        # Allow only safe characters: letters, numbers, underscore, hyphen, and dot
        safe_pattern = re.compile(r'^[a-zA-Z0-9_.-]+$')
        return bool(safe_pattern.match(module_name)) and len(module_name) <= 100

    def __register_model_type(self, package: str, project: WhtProject):
        requirement = Requirement(package)
        # special case to skip registering Python distribution as it's not a pynative model type
        if requirement.name == PYTHON_DISTRIBUTION:
            return None
        if not is_valid_package_name(requirement.name):
            raise ValueError(f"Invalid package name: {requirement.name}")

        # Additional security check: ensure module name contains only safe characters
        if not self._is_safe_module_name(requirement.name):
            raise ValueError(f"Unsafe module name: {requirement.name}")

        module = importlib.import_module(requirement.name)
        try:
            registerFunc: Callable[[WhtProject], None] = getattr(
                module, "register_extensions")
        except AttributeError:
            # register_extensions is not found in the package
            # the package is not a pynative model type
            return None

        registerFunc(project)
        return None

    @staticmethod
    def _check_requirement(line: str):
        """
        Checks if a package specified in a requirements.txt line is installed
        and meets the version constraints.
        """
        # Clean the line and ignore empty lines or comments
        line = line.strip()
        if not line or line.startswith('#'):
            print(f"Ignoring comment or empty line: '{line}'")
            return

        try:
            # Parse the line into a Requirement object. This handles specifiers like ==, >=, <
            # It returns a generator, so we get the first (and only) item.
            req = next(pkg_resources.parse_requirements(line))

            # Get the currently installed version of the package by its name
            installed_version = version(req.name)

            # Check if the installed version is compliant with the specifier set
            if not req.specifier.contains(installed_version, prereleases=True):
                raise Exception(f"Version mismatch for {req.name}: installed {installed_version}, required {req.specifier}")

        except StopIteration:
            # This can happen for lines that aren't standard package requirements (e.g., VCS links)
            print(f"Warning: Could not parse '{line}' as a standard package requirement.")
        except PackageNotFoundError:
            # The package isn't installed at all
            raise Exception(f"Not Found: {req.name} is not installed.")
        except Exception as e:
            raise Exception(f"An unexpected error occurred for line '{line}': {e}")

    def RegisterPackages(self, request: tunnel.RegisterPackagesRequest, context: grpc.ServicerContext):
        """Register packages and their model types. Called from NewWhtProject"""
        try:
            not_installed: List[str] = []
            packages = set(request.packages)
            for package in packages:
                # special case to skip checking PYTHON_DISTRIBUTION version, as that is handled by pb
                if Requirement(package).name == PYTHON_DISTRIBUTION:
                    continue

                try:
                    PythonRpcService._check_requirement(package)
                except Exception as e:
                    self.logger.error(traceback.format_exc(limit=1))
                    not_installed.append(package)

            if not_installed:
                error_message = "The following specified package(s) are not installed or their version is not correct: {}.".format(
                    ", ".join(not_installed))
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error_message)
                return tunnel.RegisterPackagesResponse()

            project = WhtProject(request.project_id, request.base_proj_ref, self.current_supported_schema_version,
                                 self.pb_version, self.ref_manager, self.gorpc)
            for package in packages:
                try:
                    self.__register_model_type(package, project)
                except Exception as e:
                    # Handle package name validation errors with appropriate error code
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details(f"Invalid package name '{package}': {str(e)}")
                    return tunnel.RegisterPackagesResponse()
            return tunnel.RegisterPackagesResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc(limit=1)
            context.set_details(tb)
            return tunnel.RegisterPackagesResponse()

    def GetPackageVersion(self, request: tunnel.GetPackageVersionRequest, context: grpc.ServicerContext):
        model_type_ref = self.ref_manager.get_object(
            request.project_id, request.model_type)
        if model_type_ref is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("model type not found")
            return tunnel.GetPackageVersionResponse()

        package = model_type_ref["package"]
        version = importlib.metadata.version(package)
        return tunnel.GetPackageVersionResponse(version=version)

    def ModelFactory(self, request: tunnel.ModelFactoryRequest, context: grpc.ServicerContext):
        try:
            model_type_ref = self.ref_manager.get_object(
                request.project_id, request.model_type)
            if model_type_ref is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("model type not found")
                return tunnel.ModelFactoryResponse()

            build_spec = json.loads(request.build_spec)
            parent_folder = WhtFolder(request.project_id, request.parent_folder_ref)
            wht_model_ref, py_model_ref, finish_pending_ref = model_type_ref["factory_func"](
                request.base_proj_ref, request.model_name, build_spec, parent_folder)
            return tunnel.ModelFactoryResponse(wht_model_ref=wht_model_ref, wht_finish_pending_ref=finish_pending_ref, python_model_ref=py_model_ref)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
            return tunnel.ModelFactoryResponse()

    # Model methods

    def GetMaterialRecipe(self, request: tunnel.GetMaterialRecipeRequest, context: grpc.ServicerContext):
        model: Optional[BaseModelType] = self.ref_manager.get_object(
            request.project_id, request.py_model_ref)
        if model is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("get metaerial recipe: model not found")
            return tunnel.GetMaterialRecipeResponse()

        try:
            recipe = model.get_material_recipe()
            recipe_ref = self.ref_manager.create_ref(
                request.project_id, recipe)
            return tunnel.GetMaterialRecipeResponse(py_recipe_ref=recipe_ref)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
            return tunnel.GetMaterialRecipeResponse()

    def DescribeRecipe(self, request: tunnel.DescribeRecipeRequest, context: grpc.ServicerContext):
        recipe: Optional[PyNativeRecipe] = self.ref_manager.get_object(
            request.project_id, request.py_recipe_ref)
        if recipe is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("describe recipe: recipe not found")
            return tunnel.DescribeRecipeResponse()

        try:
            this = WhtMaterial(request.project_id,
                               request.material_ref, "compile")
            description, extension = recipe.describe(this)
            return tunnel.DescribeRecipeResponse(description=description, extension=extension)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
            return tunnel.DescribeRecipeResponse()

    def RegisterDependencies(self, request: tunnel.RegisterDependenciesRequest, context: grpc.ServicerContext):
        """Prepare the material for execution in dry run mode. In this mode, we discover dependencies. Anything called with de_ref is considered a dependency. However, the recipe is not supposed to be actually executed. warehouse is not supposed to be hit for discovering dependencies."""
        recipe: Optional[PyNativeRecipe] = self.ref_manager.get_object(
            request.project_id, request.py_recipe_ref)
        if recipe is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("prepare recipe: recipe not found")
            return tunnel.RegisterDependenciesResponse()

        try:
            this = WhtMaterial(request.project_id,
                               request.material_ref, "compile", request.default_baseline_name)
            recipe.register_dependencies(this)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
        return tunnel.RegisterDependenciesResponse()

    def Execute(self, request: tunnel.ExecuteRequest, context: grpc.ServicerContext):
        """Prepare the recipe if necessary, and execute the recipe to create the material. In this call, it is safe to assume that dependent materials have already been executed."""
        recipe: Optional[PyNativeRecipe] = self.ref_manager.get_object(
            request.project_id, request.py_recipe_ref)
        if recipe is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("recipe not found")
            return tunnel.ExecuteResponse()

        try:
            this = WhtMaterial(request.project_id, request.material_ref, "run")
            recipe.execute(this)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
        return tunnel.ExecuteResponse()

    def GetRecipeHash(self, request: tunnel.GetRecipeHashRequest, context: grpc.ServicerContext):
        recipe: Optional[PyNativeRecipe] = self.ref_manager.get_object(
            request.project_id, request.py_recipe_ref)
        if recipe is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("recipe not found")
            return tunnel.GetRecipeHashResponse()

        try:
            hash = recipe.hash()
            return tunnel.GetRecipeHashResponse(hash=hash)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
            return tunnel.GetRecipeHashResponse()

    def Validate(self, request: tunnel.ValidateRequest, context: grpc.ServicerContext):
        model: Optional[BaseModelType] = self.ref_manager.get_object(
            request.project_id, request.py_model_ref)
        if model is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("model not found")
            return tunnel.ValidateResponse()

        try:
            isValid, reason = model.validate()
            return tunnel.ValidateResponse(valid=isValid, reason=reason)
        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(tb)
            return tunnel.ValidateResponse()

    def DeleteProjectRefs(self, request: tunnel.DeleteProjectRefsRequest, context: grpc.ServicerContext):
        self.ref_manager.delete_refs(request.project_id)
        WhtMaterial._wht_ctx_store.remove_context(request.project_id)
        return tunnel.DeleteProjectRefsResponse()

    def SanitizeBuildSpec(self, request: tunnel.SanitizeBuildSpecRequest, context: grpc.ServicerContext):
        """
        Sanitize a pynative buildspec and generate BSN messages.
        Called from Go during the parsing phase (folder.AddChildSpecs).
        """
        try:
            # Get the model type class
            model_type_ref = self.ref_manager.get_object(
                request.project_id, request.model_type)
            if model_type_ref is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"model type '{request.model_type}' not registered")
                return tunnel.SanitizeBuildSpecResponse()

            # Get the model class
            factory_func = model_type_ref.get("factory_func")
            if factory_func is None:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"factory_func not found for model type '{request.model_type}'")
                return tunnel.SanitizeBuildSpecResponse()

            # We need to find the actual model class from the factory.
            # The factory_func metadata should have the model class.
            # Let's use a different approach: find it via the registered extensions
            model_class = model_type_ref.get("model_class")
            if model_class is None:
                # Fallback: try to get it from factory metadata
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"model_class not found for model type '{request.model_type}'")
                return tunnel.SanitizeBuildSpecResponse()

            # Convert protobuf structs to Python dicts
            build_spec = json_format.MessageToDict(request.build_spec) if request.build_spec else {}
            kickstart = json_format.MessageToDict(request.kickstart) if request.kickstart else {}

            # Call the classmethod on the model class
            messages = model_class.sanitize_buildspec(
                project_id=request.project_id,
                model_type=request.model_type,
                build_spec=build_spec,
                kickstart=kickstart,
                buildspec_ref=request.buildspec_ref,
            )

            # Convert Python dicts to protobuf messages
            proto_messages = []
            for msg in messages:
                # Convert destination and payload dicts to protobuf Structs
                dest_struct = struct_pb2.Struct()
                if msg.get("destination"):
                    json_format.ParseDict(msg["destination"], dest_struct)

                payload_struct = struct_pb2.Struct()
                if msg.get("payload"):
                    json_format.ParseDict(msg["payload"], payload_struct)

                proto_msg = tunnel.BSNMessage(
                    update_type=msg.get("update_type", ""),
                    destination=dest_struct,
                    payload=payload_struct,
                    context_entity_key=msg.get("context_entity_key", ""),
                    for_parent_project=msg.get("for_parent_project", False),
                )
                proto_messages.append(proto_msg)

            return tunnel.SanitizeBuildSpecResponse(messages=proto_messages)

        except Exception as e:
            context.set_code(grpc.StatusCode.UNKNOWN)
            tb = traceback.format_exc()
            context.set_details(f"Error in SanitizeBuildSpec: {tb}")
            return tunnel.SanitizeBuildSpecResponse()

    # Ping

    def Ping(self, request, context: grpc.ServicerContext):
        return tunnel.PingResponse(message="ready")
