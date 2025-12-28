import types
from dataclasses import dataclass

from scimodels.exceptions import DependencyError

@dataclass(frozen=True)
class DependencyResult:
    name: str
    version: str | None = None
    module: types.ModuleType | None = None
    loaded: bool = False
    exception: DependencyError | None = None

    def __post_init__(self):
        if self.loaded:
            if self.module is None:
                raise ValueError("'module' cannot be None when 'loaded' is True")
            if self.exception is not None:
                raise ValueError("'error' must be None when 'loaded' is True")
        else:
            if self.module is not None:
                raise ValueError("'loaded' must the True when 'module' is not None")
            if self.exception is None:
                raise ValueError("'loaded' must be True, when 'error' is None")
            

class DepedencyLoader:
    @staticmethod
    def load(
        dependency_name: str
    ) -> DependencyResult:
        try:
            module = __import__(dependency_name)
            version = module.__version__ if hasattr(module, "__version__") else None
            return DependencyResult(
                name=dependency_name,
                version=version,
                module=module,
                loaded=True,
                exception=None
            )
        except:
            return DependencyResult(
                name=dependency_name,
                version=None,
                module=None,
                loaded=False,
                exception=DependencyError(dependency_name)
            )

    @staticmethod
    def make_exception(install_name: str) -> DependencyError:
        return DependencyError(install_name)