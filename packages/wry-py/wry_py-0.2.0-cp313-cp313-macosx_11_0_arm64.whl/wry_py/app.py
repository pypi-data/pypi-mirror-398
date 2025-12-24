from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .wry_py import UiWindow


class AppBase:
    """Base class for apps using this library.

    Subclass this and implement `render()` to build the UI tree. Use
    `set_window()` to receive the `UiWindow` the app will use. Calling
    `run()` will call `render()` once and start the window event loop.
    """

    def __init__(self) -> None:
        self.window: Optional["UiWindow"] = None

    def set_window(self, window: "UiWindow") -> None:
        """Attach a `UiWindow` to this app (called by the embedding code)."""
        self.window = window

    def render(self) -> None:
        """Build and set the root element for the window.

        Subclasses MUST override this method and call `self.window.set_root(...)`
        with the root element produced by the app.
        """
        raise NotImplementedError("Subclasses must implement render()")

    def run(self) -> None:
        """Render once and start the window event loop.

        Raises `RuntimeError` if no window has been attached.
        """
        if not self.window:
            raise RuntimeError("Window not set. Call set_window(window) before run().")
        self.render()
        # `UiWindow.run()` is implemented in the Rust extension and will
        # block until the window closes.
        self.window.run()

    def set_root(self, element) -> None:
        """Convenience: set the window root element.

        Raises `RuntimeError` if no window attached.
        """
        if not self.window:
            raise RuntimeError("Window not set. Call set_window(window) first.")
        self.window.set_root(element)

    def on_start(self) -> None:
        """Optional lifecycle hook invoked before `run()` starts."""
        return None

    def on_close(self) -> None:
        """Optional lifecycle hook invoked after the window closes."""
        return None
