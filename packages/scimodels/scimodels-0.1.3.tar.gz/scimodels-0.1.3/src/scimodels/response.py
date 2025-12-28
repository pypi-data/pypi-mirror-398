from dataclasses import dataclass

@dataclass(frozen=True)
class Response:
    # The LLM/API provider ('openai', 'gemini', etc.)
    provider: str

    # The exact model within the chosen provider
    # ('gtp-5-mini', etc.)
    model: str

    # Indicator if the response is ready
    # (if not - refetch via .refetch())
    is_ready: bool

    # Only for batch models - the fetch Batch ID
    batch_id: str | None

    # If False, all responses are linear in a 1-D list
    # If True, responses are grouped in lists, each list
    # representing a single prompt (useful when each 
    # prompt is sent multiple times via 'repeat' param)
    stacked: bool

    # The final outputs of the call; None when 'is_ready' is
    # False; Otherwise: list[str] when 'stacked' is False; 
    # list[list[str]] when 'stacked' is True 
    outputs: None | list[str] | list[list[str]]

    def __iter__(self):
        """ Iterated over the outputs if response is ready """
        if not self.is_ready or self.outputs is None:
            raise RuntimeError("Response is not ready yet")
        return iter(self.outputs)

    def __repr__(self) -> str:
        return f"scimodels.Response(provider='{self.provider}', model='{self.model}', is_ready={self.is_ready}, batch_id='{self.batch_id}', stacked={self.stacked}, outputs={self.outputs})"