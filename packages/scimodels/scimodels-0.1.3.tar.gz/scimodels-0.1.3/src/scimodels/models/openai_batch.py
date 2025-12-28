import os
import json
import string
import random

from scimodels.abstract import BatchModel
from scimodels.temp import get_temp_dir
from scimodels.dependencies import DepedencyLoader

class OpenAIBatchModel(BatchModel):
    def __init__(
        self,
        model: str,
        *,
        parallel_count: int | None = None,
        retries: int | None = None,
        temperature: float | None = 1.0,
        effort: str | None = None,
        max_tokens: int | None = None,
    ):
        self.model = model
        self.temperature = temperature
        self.effort = effort
        self.max_tokens = max_tokens
        
        if parallel_count is not None:
            raise ValueError("'parallel_count' is not supported with this model")
        if retries is not None:
            raise ValueError("'retries' is not supported with this model")
        
        # Try to load OpenAI
        dep = DepedencyLoader.load("openai")
        if not dep.loaded:
            raise dep.exception
        self._openai = dep.module

        # Check if OPENAI_API_KEY is set and issue
        # a warning if not
        if not os.getenv("OPENAI_API_KEY"):
            print("SciModels WARNING: your OPENAI_API_KEY enviromental variable is not set. This might cause issues with authentication.")

    def _send_batch(
        self, 
        queries, 
        *, 
        repeat_count = 1,
    ) -> str:
        temp_dir = get_temp_dir()

        tasks = self._make_prompts(
            queries, 
            self.model, 
            self.temperature,
            self.effort, 
            self.max_tokens, 
            repeat_count
        )
        filename = f"batch-{self._make_id(24)}.jsonl"
        filepath = os.path.join(os.getcwd(), temp_dir, filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as file:
            for obj in tasks:
                file.write(json.dumps(obj) + '\n')

        batch_file = self._openai.files.create(
            file=open(filepath, 'rb'),
            purpose="batch"
        )

        batch_job = self._openai.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )

        return batch_job.id

    def _fetch(
        self,
        batch_id, 
        *,
        repeat_count: int | None = None,
        stack: bool| None = False,
    ) -> list[str] | list[list[str]] | None:
        
        if repeat_count is not None:
            print("SciModels WARNING: This model automatically handles 'repeat_count'. Your input will be ignored.")

        res = self._openai.batches.retrieve(batch_id)

        if (res.status != "completed"):
            return None

        output_file_id = res.output_file_id
        output_file = self._openai.files.content(output_file_id).text
        output_lines = output_file.splitlines()

        if len(output_lines) == 0:
            return []

        try:
            id_init = json.loads(output_lines[0].strip())['custom_id']
        except:
            return []

        blocks_init = id_init.split('-')
        if len(blocks_init) != 4:
            return []
        
        try:
            total_count = int(blocks_init[3])
            response_count = int(blocks_init[1])
            if stack is None and response_count > 1:
                stack = True
        except:
            return []

        stacked = [[] for _ in range(total_count)]

        for line in output_lines:
            try:
                obj = json.loads(line.strip())

                if 'custom_id' not in obj:
                    continue

                blocks = obj['custom_id'].split('-')

                if len(blocks) != 4:
                    continue
            
                current_index = int(blocks[2])
                result = obj['response']['body']['choices'][0]['message']['content']
                stacked[current_index].append(result)

            except: continue

        # Fill in failed calls with None
        # (or cut if too many calls have been made)
        for lst in stacked:
            count = len(lst)
            if count < response_count:
                lst += [None for _ in range(count, response_count)]
            elif count > response_count:
                lst = lst[:response_count]

        if stack:
            return stacked
        
        unstacked = [
            elem 
            for lst in stacked
            for elem in lst
        ]

        return unstacked

    def _make_id(self, length: int) -> str:
        options = string.ascii_uppercase + string.digits
        chars = [random.choice(options) for _ in range(length)]
        return ''.join(chars)

    def _make_prompts(
        self,
        queries: list[str],
        model: str,
        temperature: float,
        effort: str | None,
        max_tokens: int | None,
        repeat_count: int
    ) -> list[dict]:
        total_count = len(queries)
        return [
            self._make_single_jsonl_prompt(
                query,
                model,
                temperature,
                max_tokens,
                repeat_index,
                repeat_count,
                total_index,
                total_count
            ) for total_index, query in enumerate(queries)
            for repeat_index in range(repeat_count)
        ]

    def _make_single_jsonl_prompt(
        self,
        query: str,
        model: str,
        temperature: float,
        max_tokens: int | None,
        repeat_index: int,
        repeat_count: int,
        total_index: int,
        total_count: int,
    ) -> dict:
        body = {
            "model": model,
            "temperature": temperature,
            "messages": [{
                "role": "user",
                "content": query
            }]
        }

        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        
        return {
            "custom_id": f"{repeat_index}-{repeat_count}-{total_index}-{total_count}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body
        }