from typing_extensions import override

from .abstract_prompt_builder import AbstractPromptBuilder
import platform
import os
import getpass
import socket


class CmdFixerAbstractPrompt(AbstractPromptBuilder):
    def __init__(self):
        prompt = ("You are an AI assistant that fixes broken shell commands. "
                  "Given a user command, provide a corrected and safe version. "
                  "Return your suggestions in a JSON array with up to {max_suggestions} items. "
                  "Do not suggest dangerous commands like 'rm -rf /' or fork bombs.")

        safety_rules = [
            "Do not suggest destructive commands like 'rm -rf /'.",
            "Do not suggest fork bombs.",
            "Only return commands that are safe to run in Linux shell."
        ]

        prompt_context = CmdFixerAbstractPrompt.get_system_info()
        number_of_suggestions = 3
        output_format = "suggestions split with ',' for example: suggestion_1 , suggestion_2 , suggestion_3"
        super().__init__(prompt, number_of_suggestions, prompt_context, safety_rules, output_format)

    @classmethod
    def get_system_info(cls) -> str:
        info = {
            "user": getpass.getuser(),
            "hostname": socket.gethostname(),
            "os": platform.system() + " " + platform.release(),
            "architecture": platform.machine(),
            "shell": os.environ.get("SHELL", "unknown"),
            "cwd": os.getcwd()
        }
        return ", ".join(f"{key}: {value}" for key, value in info.items())

    @override
    def build_prompt(self, user_input: str) -> str:
        self.context = CmdFixerAbstractPrompt.get_system_info()
        return super().build_prompt(user_input)
