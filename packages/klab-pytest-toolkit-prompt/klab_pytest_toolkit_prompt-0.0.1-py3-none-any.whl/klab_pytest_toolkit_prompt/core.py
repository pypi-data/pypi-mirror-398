import abc
from typing import Optional


class PromptInterface(abc.ABC):
    """Abstract base class for prompt interfaces."""

    @abc.abstractmethod
    def show_info(self, message: str, timeout: Optional[int] = None) -> None:
        """Display an informational message to the user."""
        raise NotImplementedError

    def confirm_action(self, message: str, timeout: Optional[int] = None) -> Optional[bool]:
        """Prompt the user to confirm an action."""
        raise NotImplementedError

    def get_user_input(self, prompt: str, timeout: Optional[int] = None) -> Optional[str]:
        """Prompt the user for input."""
        raise NotImplementedError

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        pass


class PromptFactory:
    """Factory for creating prompt interface instances."""

    class PromptType:
        UI_PROMPT = "ui_prompt"
        # Future prompt types can be added here

    @staticmethod
    def create_prompt(prompt_type: str = PromptType.UI_PROMPT) -> PromptInterface:
        """Create a prompt interface instance based on the specified type."""
        if prompt_type == PromptFactory.PromptType.UI_PROMPT:
            from klab_pytest_toolkit_prompt.ui import UiPrompt

            return UiPrompt()
        else:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")
