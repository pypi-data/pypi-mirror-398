from abc import ABC, abstractmethod


class AbstractPromptBuilder(ABC):
    def __init__(self,
                 prompt,
                 number_of_suggestions: int = 3,
                 prompt_context: str = '',
                 safety_rules: list[str] = [],
                 output_format: str = ''):
        self.prompt = prompt
        self.max_suggestions = number_of_suggestions
        self.context = prompt_context
        self.safety_rules = safety_rules
        self.output_format = output_format

    def build_prompt(self, user_input: str) -> str:
        """
        Build and return the prompt string based on user input.

        Must be implemented in all subclasses.
        """
        return (
            f"Your job is: {self.prompt}\n"
            f"Safety rules to follow: {', '.join(self.safety_rules)}\n"
            f"System context: {self.context}\n"
            f"User request: {user_input}\n"
            f"Output format: {self.output_format}\n"
            f"Return at most {self.max_suggestions} suggestions. "
            f"If fewer suggestions are enough, return only what is necessary."
        )
