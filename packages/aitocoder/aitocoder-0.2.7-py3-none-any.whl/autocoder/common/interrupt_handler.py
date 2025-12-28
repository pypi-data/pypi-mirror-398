"""
Interrupt Handler Module for AitoCoder
(NEW)
This module provides a robust mechanism for handling keyboard interrupts (Ctrl+C)
during task execution. It ensures that:
1. SIGINT signals are properly caught even when prompt_toolkit is active
2. All running tasks are cancelled via the global_cancel system
3. Control returns immediately to the REPL

Usage:
    from autocoder.common.interrupt_handler import InterruptHandler

    handler = InterruptHandler(task_event)
    handler.install()
    try:
        # ... run tasks ...
    finally:
        handler.uninstall()
"""

import signal
import threading
from typing import Optional, Callable, Any
from rich.console import Console
from rich.prompt import Prompt


class InterruptHandler:
    """
    A thread-safe interrupt handler that manages SIGINT (Ctrl+C) signals.

    When a task is running (determined by task_event), pressing Ctrl+C will:
    1. Set the cancellation flag for all active tokens
    2. Print a cancellation message
    3. Allow the task to gracefully terminate

    When no task is running, the default behavior is preserved.
    """

    def __init__(
        self,
        task_event: Any = None,
        on_interrupt: Optional[Callable[[], None]] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize the interrupt handler.

        Args:
            task_event: A TaskEvent object that tracks task state (has is_running() method)
            on_interrupt: Optional callback to execute when interrupt is triggered
            console: Optional Rich console for output
        """
        self._task_event = task_event
        self._on_interrupt = on_interrupt
        self._console = console or Console()
        self._original_handler = None
        self._lock = threading.Lock()
        self._interrupt_count = 0
        self._installed = False
        self._last_interrupt_time = 0

    def install(self) -> None:
        """Install the custom SIGINT handler."""
        with self._lock:
            if self._installed:
                return

            # Store the original handler
            self._original_handler = signal.getsignal(signal.SIGINT)

            # Install our custom handler
            signal.signal(signal.SIGINT, self._handle_interrupt)
            self._installed = True

    def uninstall(self) -> None:
        """Restore the original SIGINT handler."""
        with self._lock:
            if not self._installed:
                return

            if self._original_handler is not None:
                signal.signal(signal.SIGINT, self._original_handler)
            else:
                signal.signal(signal.SIGINT, signal.SIG_DFL)

            self._installed = False
            self._original_handler = None

    def _handle_interrupt(self, signum: int, frame: Any) -> None:
        """
        Handle SIGINT signal.

        This method is called when Ctrl+C is pressed. It checks if a task
        is running and triggers cancellation if so.
        """
        import time
        current_time = time.time()

        # Prevent rapid-fire interrupts (debounce)
        if current_time - self._last_interrupt_time < 0.5:
            return
        self._last_interrupt_time = current_time

        with self._lock:
            self._interrupt_count += 1

        # Check if a task is running
        is_task_running = False
        if self._task_event is not None:
            try:
                is_task_running = self._task_event.is_running()
            except Exception:
                pass

        if is_task_running:
            # Task is running - trigger cancellation
            self._trigger_cancellation()
        else:
            # No task running - use default behavior or pass to original handler
            if self._original_handler is not None and callable(self._original_handler):
                try:
                    self._original_handler(signum, frame)
                except Exception:
                    pass
            else:
                # Default: raise KeyboardInterrupt
                raise KeyboardInterrupt("User interrupted")

    def _trigger_cancellation(self) -> None:
        """Trigger cancellation of all active tasks."""
        try:
            from autocoder.common.global_cancel import global_cancel

            # Cancel all active tokens
            global_cancel.set_active_tokens()

            # Print cancellation message
            self._console.print("\n[yellow]Cancelling current operation...[/yellow]")
            # name = Prompt.ask("Are you sure", default="", show_default=False)

            # Execute custom callback if provided
            if self._on_interrupt is not None:
                try:
                    self._on_interrupt()
                except Exception:
                    pass

        except Exception as e:
            # Fallback: just print a message
            print(f"\nInterrupt received (error: {e})")

    def trigger_from_keybinding(self) -> bool:
        """
        Trigger cancellation from a keybinding handler.

        This method is called from the prompt_toolkit Ctrl+C keybinding
        when a task is running.

        Returns:
            True if cancellation was triggered, False otherwise
        """
        is_task_running = False
        if self._task_event is not None:
            try:
                is_task_running = self._task_event.is_running()
            except Exception:
                pass

        if is_task_running:
            self._trigger_cancellation()
            return True
        return False

    def get_interrupt_count(self) -> int:
        """Get the number of interrupts received."""
        with self._lock:
            return self._interrupt_count

    def reset_interrupt_count(self) -> None:
        """Reset the interrupt counter."""
        with self._lock:
            self._interrupt_count = 0


# Global singleton instance (will be initialized in run_app)
_global_interrupt_handler: Optional[InterruptHandler] = None


def get_interrupt_handler() -> Optional[InterruptHandler]:
    """Get the global interrupt handler instance."""
    return _global_interrupt_handler


def set_interrupt_handler(handler: InterruptHandler) -> None:
    """Set the global interrupt handler instance."""
    global _global_interrupt_handler
    _global_interrupt_handler = handler


def trigger_cancellation_from_keybinding() -> bool:
    """
    Convenience function to trigger cancellation from a keybinding.

    Returns:
        True if cancellation was triggered, False otherwise
    """
    handler = get_interrupt_handler()
    if handler is not None:
        return handler.trigger_from_keybinding()
    return False
