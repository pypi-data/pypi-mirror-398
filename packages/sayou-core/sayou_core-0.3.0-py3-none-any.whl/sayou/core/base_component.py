import logging
from abc import ABC
from typing import List

from .callbacks import BaseCallback


class BaseComponent(ABC):
    """
    The foundational base class for all Sayou components.

    Provides standardized logging, configuration management, and an event
    observation mechanism (Callback System).
    """

    component_name: str = "BaseComponent"

    def __init__(self):
        """
        Initialize the component with a logger and an empty callback list.
        """
        self.logger = logging.getLogger(self.component_name)
        self.logger.propagate = False

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        self._callbacks: List[BaseCallback] = []

    def initialize(self, **kwargs):
        """
        (Optional) Register any settings or states required for initialization.
        """
        pass

    def _log(self, msg: str, level: str = "info"):
        if level.lower() == "debug":
            self.logger.debug(msg)
        elif level.lower() == "warning":
            self.logger.warning(msg)
        elif level.lower() == "error":
            self.logger.error(msg)
        else:
            self.logger.info(msg)

    def __repr__(self):
        return f"<{self.component_name}>"

    # -------------------------------------------------------------------------
    # Callback / Observer Pattern Implementation
    # -------------------------------------------------------------------------

    def add_callback(self, callback: BaseCallback):
        """
        Registers a callback listener to this component.

        Args:
            callback (BaseCallback): An instance of a class inheriting from BaseCallback.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _emit(self, event_method: str, **kwargs):
        """
        Broadcasts an event to all registered callbacks.

        This method dynamically invokes the specified method name on each
        callback instance if it exists.

        Args:
            event_method (str): The method name to call on the callback
                                (e.g., 'on_start', 'on_finish').
            **kwargs: Arguments to pass to the callback method.
        """
        for callback in self._callbacks:
            handler = getattr(callback, event_method, None)
            if callable(handler):
                try:
                    handler(component_name=self.component_name, **kwargs)
                except Exception as e:
                    self._log(
                        f"Error in callback {type(callback).__name__}: {e}",
                        level="warning",
                    )
