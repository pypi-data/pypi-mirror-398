from typing import Dict, Any, Union
import re

class RefManager:
    def __init__(self):
        self.refs_dict: Dict[int, Dict[Union[str, int], Any]] = {}
        self.max_allocated_id = 1

    def create_ref(self, project_id: int, obj: Any):
        ref_id = self.max_allocated_id
        if project_id not in self.refs_dict:
            self.refs_dict[project_id] = {}
        self.refs_dict[project_id][ref_id] = obj
        self.max_allocated_id += 1
        return ref_id

    def create_ref_with_key(self, project_id: int, key: str, obj: Any):
        if project_id not in self.refs_dict:
            self.refs_dict[project_id] = {}
        self.refs_dict[project_id][key] = obj

    def get_object(self, project_id: int, ref_id: Union[str, int]):
        if project_id not in self.refs_dict:
            raise Exception(f"Project with project_id: {project_id} not found")
        return self.refs_dict[project_id].get(ref_id, None)

    def delete_refs(self, project_id: int):
        self.refs_dict[project_id].pop(project_id, None)

def is_valid_package_name(package_name: str) -> bool:
        """
        Validate package name to prevent code injection.
        Package names should only contain alphanumeric characters, hyphens, underscores, and dots.
        """
        if not package_name or len(package_name) > 214:  # PyPI package name limit
            return False
        
        # Allow only safe characters for package names
        # This regex matches valid Python package naming conventions
        # and prevents path traversal: No ../ or / characters allowed
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$'
        return bool(re.match(pattern, package_name))