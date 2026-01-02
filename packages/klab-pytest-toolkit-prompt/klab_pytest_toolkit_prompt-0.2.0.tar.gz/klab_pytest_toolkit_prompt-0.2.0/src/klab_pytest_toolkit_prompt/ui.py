import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Any, Callable, Optional, TypeVar

from klab_pytest_toolkit_prompt.core import PromptInterface

T = TypeVar("T")


class UiPrompt(PromptInterface):
    """Concrete implementation of PromptInterface for UI prompts.

    The implementation will be done with tkinter, because it is included in the standard library.
    """

    def _run_dialog(
        self,
        dialog_fn: Callable[[tk.Tk], T],
        timeout: Optional[int] = None,
        default: Optional[T] = None,
    ) -> Optional[T]:
        """Run a dialog with optional timeout handling.

        Args:
            dialog_fn: Function that takes root window and returns dialog result
            timeout: Optional timeout in seconds
            default: Default value to return on timeout or error

        Returns:
            The dialog result or default value
        """
        result: Any = default
        timeout_expired = False

        def show():
            nonlocal result, timeout_expired
            root = tk.Tk()
            root.withdraw()
            root.update_idletasks()

            if timeout:

                def auto_close():
                    nonlocal timeout_expired
                    timeout_expired = True
                    self._safe_destroy(root)

                root.after(timeout * 1000, auto_close)

            try:
                dialog_result = dialog_fn(root)
                if not timeout_expired:
                    result = dialog_result
            except tk.TclError:
                pass

            self._safe_destroy(root)

        show()
        return result

    @staticmethod
    def _safe_destroy(root: tk.Tk) -> None:
        """Safely quit and destroy a tkinter root window."""
        try:
            root.quit()
            root.destroy()
        except tk.TclError:
            pass

    def show_info(self, message: str, timeout: Optional[int] = None) -> None:
        """Display an informational message to the user.

        Args:
            message: The message to display
            timeout: Optional timeout in seconds. If provided, the dialog will
                    automatically close after this time.
        """
        self._run_dialog(
            lambda root: messagebox.showinfo("Information", message, parent=root),
            timeout=timeout,
        )

    def confirm_action(self, message: str, timeout: Optional[int] = None) -> Optional[bool]:
        """Prompt the user to confirm an action.

        Args:
            message: The confirmation message to display
            timeout: Optional timeout in seconds. If provided and expires,
                    returns False (no confirmation).

        Returns:
            bool: True if user confirmed (clicked Yes/OK), False otherwise
        """
        return self._run_dialog(
            lambda root: messagebox.askyesno("Confirm Action", message, parent=root),
            timeout=timeout,
            default=False,
        )

    def get_user_input(self, prompt: str, timeout: Optional[int] = None) -> Optional[str]:
        """Prompt the user for input.

        Args:
            prompt: The prompt message to display
            timeout: Optional timeout in seconds. If provided and expires,
                    returns None.

        Returns:
            Optional[str]: The user input, or None if cancelled or timed out
        """
        return self._run_dialog(
            lambda root: simpledialog.askstring("Input Required", prompt, parent=root),
            timeout=timeout,
            default=None,
        )
