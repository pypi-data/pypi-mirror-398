from abc import abstractmethod

from scimodels.response import Response
from scimodels.abstract.modelbase import Model

class BatchModel(Model):
    @property
    def is_batch(self) -> bool:
        return True

    def fetch(
        self,
        batch_id: str,
        *,
        repeat_count: int | None = None,
        stack: bool | None = None,
    ) -> Response:
        super()._ensure_values()
        
        if repeat_count is not None and repeat_count < 1:
            raise ValueError("'repeat_count' must be greater or equal to 1")    
    
        if stack == False and repeat_count is not None and repeat_count > 1:
            raise ValueError("When 'repeat_count' is greater than 1, 'stack' cannot be False")
        
        if stack is None and repeat_count is not None:
            if repeat_count == 1:
                stack = False
            else:
                stack = True
                
        outputs = self._fetch(
            batch_id, 
            repeat_count=repeat_count,
            stack=stack,
        )

        if outputs is None:
            return Response(
                provider=self.provider,
                model=self.model,
                is_ready=False,
                batch_id=batch_id,
                stacked=False,
                outputs=None
            ) 
       
        prestacked = False

        if len(outputs) != 0:
            if isinstance(outputs[0], list):
                stack = True
                prestacked = True

        if stack and not prestacked:
            if repeat_count is None:
                raise ValueError("This model did not automatically handle 'repeat_count', so you must specify it")
            if len(outputs) % repeat_count != 0:
                raise RuntimeError("Invalid 'repeat_count' does not divide number of outputs")
            query_count = len(outputs) / repeat_count
            outputs = [
                outputs[i * repeat_count:(i + 1) * repeat_count]
                for i in range(len(query_count))
            ]

        return Response(
            provider=self.provider,
            model=self.model,
            is_ready=True,
            batch_id=batch_id,
            stacked=(False if stack is None else stack),
            outputs=outputs
        )

    @abstractmethod
    def _fetch(
        self,
        batch_id: str,
        *,
        repeat_count: int | None = None,
        stack: bool | None = None,
    ) -> list[str] | list[list[str]] | None:
        pass

    def _send(
        self,
        queries: list[str],
        *,
        repeat_count: int | None = None,
        stack: bool | None = None,
    ) -> Response:
        if stack is not None:
            raise ValueError("In batch models .send() does not support 'stack'")

        batch_id = self._send_batch(
            queries,
            repeat_count=repeat_count,
        )

        return Response(
            provider=self.provider,
            model=self.model,
            is_ready=False,
            batch_id=batch_id,
            stacked=False,
            outputs=None
        )

    @abstractmethod
    def _send_batch(
        self,
        queries: list[str],
        *,
        repeat_count: int | None = None,
    ) -> str:
        pass