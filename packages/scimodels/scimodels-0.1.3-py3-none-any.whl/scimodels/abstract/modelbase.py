from abc import ABC, abstractmethod

from scimodels.response import Response
from scimodels.temp import clear_temp_dir

class Model(ABC):
    def send(
        self,
        queries: str | list[str],
        *,
        repeat_count: int | None = None,
        stack: bool | None = None
    ) -> Response:
        self._ensure_values()
        clear_temp_dir()

        if repeat_count is None:
            repeat_count = 1

        if repeat_count < 1:
            raise ValueError("'repeat_count' must be greater or equal to 1")    
    
        if stack == False and repeat_count > 1:
            raise ValueError("When 'repeat_count' is greater than 1, 'stack' cannot be False")
        
        if stack is None and not self.is_batch:
            if repeat_count == 1:
                stack = False
            else:
                stack = True

        queries = [queries] if isinstance(queries, str) else queries

        return self._send(
            queries,
            repeat_count=repeat_count,
            stack=stack
        )
    
    @property
    def is_batch(self) -> bool:
        return False

    @abstractmethod
    def _send(
        self,
        queries: list[str],
        *,
        repeat_count: int | None = None,
        stack: bool | None = None
    ) -> Response:
        pass

    def fetch(
        self,
        batch_id: str,
        *,
        repeat_count: int | None = None,
        stack: bool | None = None
    ) -> Response:
        raise RuntimeError("The .fetch() method is only supported by batch models.")
    
    def _ensure_values(self) -> None:
        if not hasattr(self, "provider"):
            self.provider = None
        if not hasattr(self, "model"):
            self.model = None