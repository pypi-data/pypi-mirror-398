COMPONENT_REGISTRY = {
    # Connector Group
    "generator": {},
    "fetcher": {},
    # Document Group
    "parser": {},
    "converter": {},
    "ocr": {},
    # Refinery Group
    "normalizer": {},
    "processor": {},
    # Chunking Group
    "splitter": {},
    # Wrapper Group
    "adapter": {},
    # Assembler Group
    "builder": {},
    # Loader Group
    "writer": {},
    # Extractor Group
    # LLM Group
    # Visualizer Group
    "tracer": {},
    "renderer": {},
}


def register_component(role: str):
    """
    Registers a component class into the global component registry.

    This decorator adds the decorated class to the `COMPONENT_REGISTRY`
    under the specified role. It uses the class's `component_name` attribute
    as the unique key within that role.

    Args:
        role (str): The category or role of the component (e.g., "generator", "fetcher").
                    Must be one of the pre-defined keys in `COMPONENT_REGISTRY`.

    Returns:
        Callable: The decorator function to apply to the component class.

    Raises:
        ValueError: If the provided `role` is not a valid key in the registry.
    """

    def decorator(cls):
        if role not in COMPONENT_REGISTRY:
            raise ValueError(
                f"Unknown component role: '{role}'. defined roles: {list(COMPONENT_REGISTRY.keys())}"
            )

        if hasattr(cls, "component_name"):
            COMPONENT_REGISTRY[role][cls.component_name] = cls
        return cls

    return decorator
