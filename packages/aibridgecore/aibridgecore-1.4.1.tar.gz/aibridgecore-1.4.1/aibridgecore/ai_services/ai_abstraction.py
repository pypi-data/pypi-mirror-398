from abc import ABC, abstractmethod


class AIInterface(ABC):
    @abstractmethod
    def generate(
        self,
        prompts,
        prompt_ids,
        prompt_data,
        variables,
        model,
        variation_count,
        max_tokens,
        temperature,
    ):
        pass

    @abstractmethod
    def get_response(
        self,
        prompts,
        model,
        variation_count,
        max_tokens,
        temperature,
    ):
        pass
