from abc import abstractmethod
from concurrent.futures import (
    ThreadPoolExecutor, 
    wait, 
    FIRST_COMPLETED,
)
import time

from tqdm import tqdm

from scimodels.exceptions import MissingParameterError
from scimodels.response import Response
from scimodels.abstract.modelbase import Model

class _Scheduler:
    # Initialize when _Scheduler with a pointer to function 
    # that executes the requests. First argument of that 
    # function must be a prompt string to be send and it 
    # must return a list of responses
    def __init__(
        self, 
        function, 
        concurrent_requests: int | None = 1, 
        max_retries: int | None = 1, 
        show_progress_bar: bool = False,
        delay: float | None = 0.1
    ):
        self.function = function
        self.concurrent_requests = concurrent_requests
        self.max_retries = max_retries
        self.show_progress_bar = show_progress_bar
        self.delay = delay
    
    # Run prompts through the function
    def run_queries(
        self, 
        queries: list[str], 
        *args,
        **kwargs
    ):
        total = len(queries)
        completed = 0
        output = [None for _ in range(total)]

        pbar = tqdm(
            total=total,
            desc="Prompts",
            unit="req",
            disable=not self.show_progress_bar,
        )

        with ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
            future_to_index = {
                executor.submit(self.run_with_retries, query, *args, **kwargs): i
                for i, query in enumerate(queries)
            }

            try:
                while future_to_index:
                    done, _ = wait(
                        future_to_index.keys(), timeout=0.2,
                        return_when=FIRST_COMPLETED
                    )
                    for future in done:
                        idx = future_to_index.pop(future)
                        output[idx] = future.result()
                        pbar.update(1)
                        completed += 1
                        if completed == total:
                            return output
            except KeyboardInterrupt:
                print("Interrupted by user. Shutting down...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise

    # Implement retries
    def run_with_retries(
        self, 
        *args,
        **kwargs
    ) -> list[str] | None:
        try_cnt = 0
        while try_cnt < self.max_retries:
            try:
                output = self.function(*args, **kwargs)
                time.sleep(self.delay)
                if output is not None:
                    return output
                try_cnt += 1
            except Exception as e:
                print(e)
                time.sleep(self.delay)
                # if api error is not due to rate limit, try again
                if "rate limit" not in str(e).lower() and "429" not in str(e):
                    try_cnt += 1
        return None

class APIModel(Model):
    def _check_params(self) -> None:
        if not hasattr(self, "parallel_count"):
            raise MissingParameterError(self, "parallel_count")
        if not hasattr(self, "retries"):
            raise MissingParameterError(self, "retries")
        if not hasattr(self, "show_progress_bar"):
            self.show_progress_bar = False

    def _send(
        self,
        queries: list[str],
        *,
        repeat_count: int | None = None,
        stack: bool | None = None,
    ) -> Response:
        self._check_params()

        parallel_count = self.parallel_count
        retries = self.retries

        scheduler = _Scheduler(
            self._retrieve_response, 
            parallel_count, 
            retries,
            show_progress_bar=self.show_progress_bar,
        )

        final_queries = [
            query
            for query in queries
            for _ in range(repeat_count if repeat_count else 1)
        ]

        outputs = scheduler.run_queries(final_queries)

        if stack:
            outputs = [
                outputs[i * repeat_count:(i + 1) * repeat_count]
                for i in range(len(queries))
            ]
        
        return Response(
            provider=self.provider,
            model=self.model,
            is_ready=True,
            batch_id=None,
            stacked=stack,
            outputs=outputs
        )
        
    @abstractmethod
    def _retrieve_response(
        self,
        query: str
    ) -> str | None:
        pass