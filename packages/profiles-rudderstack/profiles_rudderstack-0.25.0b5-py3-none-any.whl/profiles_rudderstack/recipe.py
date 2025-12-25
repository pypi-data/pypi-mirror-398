import hashlib
from inspect import getsource
from typing import Tuple
from abc import ABC, abstractmethod
from profiles_rudderstack.material import WhtMaterial
from profiles_rudderstack.reader import Reader


class PyNativeRecipe(ABC):
    def __init__(self):
        self.reader = Reader()

    @abstractmethod
    def register_dependencies(self, this: WhtMaterial):
        """Prepare the material for execution in dry run mode. In this mode, we discover dependencies. Anything called with de_ref is considered a dependency. However, the recipe is not supposed to be actually executed.

        Args:
            this (WhtMaterial): The material to be prepared
        """
        raise NotImplementedError()

    @abstractmethod
    def execute(self, this: WhtMaterial):
        """Prepare the recipe if necessary, and execute the recipe to create the material. In this call, it is safe to assume that dependent materials have already been executed.

        Args:
            this (WhtMaterial): The material to be executed
        """
        raise NotImplementedError()

    @abstractmethod
    def describe(self, this: WhtMaterial) -> Tuple[str, str]:
        """Describe the material

        Args:
            this (WhtMaterial): The material to be described

        Returns:
            Tuple[str, str]: The content and extension of the material to be described
        """
        raise NotImplementedError()

    def hash(self):
        prepareCode = getsource(self.register_dependencies)
        executeCode = getsource(self.execute)
        describeCode = getsource(self.describe)

        hash = hashlib.sha256()
        hash.update(prepareCode.encode('utf-8'))
        hash.update(executeCode.encode('utf-8'))
        hash.update(describeCode.encode('utf-8'))

        return hash.hexdigest()
    
class NoOpRecipe(PyNativeRecipe):
    def register_dependencies(self, this: WhtMaterial):
        pass

    def execute(self, this: WhtMaterial):
        pass

    def describe(self, this: WhtMaterial) -> Tuple[str, str]:
        return "", ""
