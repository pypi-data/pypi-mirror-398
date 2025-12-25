from ctypes import Union
from typing import Tuple, Optional, List, Union
from abc import ABC, abstractmethod
from profiles_rudderstack.recipe import PyNativeRecipe
from typing import NamedTuple, Dict, Any


class MaterializationBuildSpec(NamedTuple):
    output_type: str
    run_type: str
    requested_enable_status: str


class EntityId(NamedTuple):
    select: str = ""
    type: str = ""
    entity: str = ""
    to_default_stitcher: bool = False
    as_col: str = ""


class FeatureMetadata(NamedTuple):
    name: str = ""
    description: str = ""


class BaseModelType(ABC):
    TypeName = "base_model_type"
    # Json Schema
    BuildSpecSchema = {}

    display_name: str = ""
    contract: Optional[Union[str, Dict[str, Any]]] = None
    entity_key: Optional[str] = None
    cohort_path: Optional[str] = None
    materialization: Optional[MaterializationBuildSpec] = None
    ids: Optional[List[EntityId]] = None
    features: Optional[List[FeatureMetadata]] = None

    def __init__(self, build_spec: Dict[Any, Any], schema_version: int, pb_version: str) -> None:
        self.build_spec = build_spec
        self.schema_version = schema_version
        self.pb_version = pb_version

        if build_spec.get("display_name", None) is not None:
            self.display_name = build_spec["display_name"]

        if build_spec.get("entity_key", None) is not None:
            self.entity_key = build_spec["entity_key"]

        if build_spec.get("entity_cohort", None) is not None:
            self.cohort_path = build_spec["entity_cohort"]

        if build_spec.get("time_grain", None) is not None:
            self.time_grain = build_spec["time_grain"]

        if build_spec.get("contract", None) is not None:
            self.contract = build_spec["contract"]

        if build_spec.get("features", None) is not None:
            self.features = []
            for feature in build_spec["features"]:
                self.features.append(FeatureMetadata(
                    feature["name"], feature.get("description", "")
                ))

        mzn = build_spec.get("materialization", None)
        if mzn is not None:
            self.materialization = MaterializationBuildSpec(mzn.get(
                "output_type", ""), mzn.get("run_type", ""), mzn.get("requested_enable_status", ""))

        if build_spec.get("ids", None) is not None:
            self.ids = []
            for id in build_spec["ids"]:
                self.ids.append(EntityId(
                    id["select"], id["type"], id["entity"], id.get("to_default_stitcher", False), id.get("as_col", "")))

    @abstractmethod
    def get_material_recipe(self) -> PyNativeRecipe:
        """Define the material recipe of the model

        Returns:
            Recipe: Material recipe of the model
        """
        raise NotImplementedError()

    @classmethod
    def sanitize_buildspec(
        cls,
        project_id: int,
        model_type: str,
        build_spec: Dict[Any, Any],
        kickstart: Dict[Any, Any],
        buildspec_ref: int,
    ) -> List[Dict[str, Any]]:
        """
        Sanitize the buildspec and generate BSN messages.
        This is called during the parsing phase to generate initial messages.

        Default implementation:
        1. Calls Go-side SanitizeBase to get base messages (LinkCohortFeature, etc.)
        2. Subclasses can override to add their own messages (e.g., for dynamic child creation)

        Args:
            project_id: The project ID
            model_type: The model type name
            build_spec: The raw build specification dict
            kickstart: Kickstart information from Go
            buildspec_ref: Reference to the Go PyNativeModelBuildSpec object

        Returns:
            List of BSN messages (each message is a dict with keys: update_type, destination, payload, context_entity_key, for_parent_project)
        """
        from profiles_rudderstack.tunnel import client as tunnel_client

        # Call Go-side SanitizeBase to get base messages
        base_messages = tunnel_client.sanitize_base(
            project_id=project_id,
            buildspec_ref=buildspec_ref,
            model_type=model_type,
        )

        # Subclasses can override this method to add their own messages
        # Default: just return base messages
        return base_messages

    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """Validate the model

        Returns:
            Tuple[bool, str]: Validation result and error message
        """
        if self.schema_version < 43:
            return False, "schema version should >= 43"
        return True, ""
