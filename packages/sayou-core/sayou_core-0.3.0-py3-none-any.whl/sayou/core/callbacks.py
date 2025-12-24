from typing import Any


class BaseCallback:
    """
    Abstract base class for event handling across the Sayou ecosystem.

    This interface defines the standard hooks that any component (Connector,
    Refinery, Loader, etc.) can trigger. Observers (like Visualizers or Loggers)
    should inherit from this class and override the methods they are interested in.
    """

    def on_start(self, component_name: str, input_data: Any, **kwargs):
        """
        Triggered when a component starts processing a unit of work.

        Args:
            component_name (str): The name of the component emitting the event.
            input_data (Any): The input payload being processed.
                            (e.g., SayouTask for Connector, Document for Refinery).
            **kwargs: Additional context-specific metadata.
        """
        pass

    def on_finish(self, component_name: str, result_data: Any, success: bool, **kwargs):
        """
        Triggered when a component finishes processing a unit of work.

        Args:
            component_name (str): The name of the component emitting the event.
            result_data (Any): The output payload produced by the component.
                            (e.g., SayouPacket for Connector, Chunk for Refinery).
            success (bool): Whether the operation was successful.
            **kwargs: Additional context-specific metadata (e.g., execution time).
        """
        pass

    def on_error(self, component_name: str, error: Exception, **kwargs):
        """
        Triggered when an exception occurs during processing.

        Args:
            component_name (str): The name of the component where the error occurred.
            error (Exception): The exception object caught.
            **kwargs: Additional context-specific metadata.
        """
        pass

    def on_event(self, event_name: str, payload: Any = None, **kwargs):
        """
        Triggered for custom or generic events not covered by start/finish.

        Use this for granular updates like 'progress_update', 'state_change', etc.

        Args:
            event_name (str): The identifier of the custom event.
            payload (Any, optional): Data associated with the event.
            **kwargs: Additional metadata.
        """
        pass
