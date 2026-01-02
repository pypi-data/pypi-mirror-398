def __getattr__(name):
    """Lazy imports for VLM module to avoid gradio_client dependency."""
    if name == "OmniParserClient":
        from ._client import OmniParserClient
        return OmniParserClient
    elif name == "OmniParserError":
        from ._client import OmniParserError
        return OmniParserError
    elif name == "OmniParserElement":
        from ._parser import OmniParserElement
        return OmniParserElement
    elif name == "OmniParserResultProcessor":
        from ._parser import OmniParserResultProcessor
        return OmniParserResultProcessor
    elif name == "OmniParserElementSelector":
        from ._selector import OmniParserElementSelector
        return OmniParserElementSelector
    elif name == "OmniParserOrchestrator":
        from .interface import OmniParserOrchestrator
        return OmniParserOrchestrator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "OmniParserClient",
    "OmniParserError",
    "OmniParserElement",
    "OmniParserResultProcessor",
    "OmniParserElementSelector",
    "OmniParserOrchestrator",
]

