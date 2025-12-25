from abc import ABC, abstractmethod
from ..prompt.abstract_prompt_builder import AbstractPromptBuilder


class AbstractLLMModel(ABC):
    def __init__(
            self,
            model_name: str,
            prompt_builder: AbstractPromptBuilder,
            api_key: str | None = None
    ):
        if not isinstance(prompt_builder, AbstractPromptBuilder):
            raise TypeError(
                "prompt_builder must be an instance of AbstractPromptBuilder"
            )

        self.model_name = model_name
        self.api_key = api_key
        self.prompt_builder = prompt_builder

    @abstractmethod
    def _make_request(self, prompt: str) -> str:
        """
        Sends the final prompt to the LLM provider.
        Must be implemented by subclasses.
        """
        pass

    def send_request(self, user_input: str) -> list[str]:
        """
        Builds the prompt using the prompt builder
        and sends it to the LLM.
        """
        full_prompt = self.prompt_builder.build_prompt(user_input)
        return self._make_request(full_prompt)
