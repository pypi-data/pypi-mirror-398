from scimodels.abstract import Model
from scimodels.response import Response
from scimodels.dependencies import DepedencyLoader

class vLLMModel(Model):

    def __init__(
        self,
        model: str,
        *,
        parallel_count: int = 1,
        retries: int | None = None,
        temperature: float = 0.6,
        reasoning_effort: str | None = None,
        max_tokens: int | None = None,
        context_length: int = 2048,
        do_init: bool = True,
    ):
        self.provider = None
        self._model = model
        self._temperature = temperature
        self._effort = reasoning_effort
        self._max_tokens = max_tokens
        self._context_length = context_length
        self._parallel_count = parallel_count
        
        if retries is not None:
            raise ValueError("'retries' is not supported with this model")

        # Try to load vLLM
        vllm = DepedencyLoader.load("vllm")
        if not vllm.loaded:
            raise vllm.exception
        
        # Try to load transformers
        transformers = DepedencyLoader.load("transformers")
        if not transformers.loaded:
            raise transformers.exception

        self._vllm = vllm.module
        self._transformers = transformers.module

        if do_init:
            self.initialize()

    def initialize(self) -> None:
        LLM = self._vllm.LLM
        SamplingParams = self._vllm.SamplingParams

        self._llm = LLM(
            model=self._model,
            gpu_memory_utilization=0.9,
            max_model_len=self._context_length,
            tensor_parallel_size=self._parallel_count,
        )

        params = {"temperature": self._temperature}

        if self._max_tokens:
            params["max_tokens"] = self._max_tokens
        
        self._tokenizer = self._transformers.AutoTokenizer.from_pretrained(self._model)
        self._params = SamplingParams(**params)

    def _send(
        self,
        queries: list[str],
        *,
        repeat_count: int = 1,
        stack: bool | None = False,
    ) -> Response:
        queries = [
            query for query in queries
            for _ in range(repeat_count)
        ]

        templates = [{
            "role": "user",
            "content": query
        } for query in queries]

        tokenizer_params = {}

        if self._effort:
            tokenizer_params["reasoning_effort"] = self._effort

        prefills = [self._tokenizer.apply_chat_template(
            [query],
            tokenize=False,
            add_generation_prompt=True,
            **tokenizer_params
        ) for query in templates]

        outputs = self._llm.generate(prefills, self._params)
        outputs = [output.outputs[0].text.strip() for output in outputs]

        if stack:
            outputs = [
                outputs[i * repeat_count:(i + 1) * repeat_count]
                for i in range(len(queries))
            ]

        return Response(
            provider=self.provider,
            model=self._model,
            is_ready=True,
            batch_id=None,
            stacked=stack,
            outputs=outputs
        )