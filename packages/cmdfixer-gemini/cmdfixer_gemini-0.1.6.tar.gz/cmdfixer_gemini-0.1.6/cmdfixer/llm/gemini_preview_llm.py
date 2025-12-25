from typing_extensions import override
from .abstract_llm_model import AbstractLLMModel
from ..prompt.cmd_fix_prompt import CmdFixerAbstractPrompt
from google import genai
import json
import os


class GeminiPreviewLLM(AbstractLLMModel):
    def __init__(self):
        super().__init__('gemini_preview_llm', CmdFixerAbstractPrompt(), os.environ.get('GEMINI_API_KEY'))
        self.client = genai.Client(api_key=self.api_key)

    def _process_response(self, response_text: str) -> list[str]:
        tmp = response_text.find('json')
        response_text = response_text[tmp + 4:-3]
        return json.loads(response_text)

    @override
    def _make_request(self, prompt: str) -> list[str]:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        ).text
        return self._process_response(response)
