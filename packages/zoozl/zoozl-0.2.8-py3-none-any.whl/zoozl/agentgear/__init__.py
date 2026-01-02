"""Package containing helpfull methods for OpenAI agent definitions.

Usage examples:

    >>> class MyAgent(BaseAgent): pass
    >>> ai_client = OpenAI(api_key=api_key)
    >>> agents = configure(OpenAI(api_key=api_key), [MyAgent])
"""

from .tools import BaseAgent, configure, StreamHandler, FunctionSchema


__all__ = ["BaseAgent", "configure", "StreamHandler", "FunctionSchema"]
