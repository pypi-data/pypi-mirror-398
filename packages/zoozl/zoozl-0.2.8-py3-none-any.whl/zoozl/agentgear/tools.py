"""Base definitions for agents."""

import enum
import hashlib
import logging
import json
from typing import Iterator, Optional

from openai import OpenAI, AssistantEventHandler
import pydantic

import zoozl.chatbot


log = logging.getLogger(__name__)


class BaseAgent:
    """Base agent class.

    All agents must subclass this class.
    """

    name = None
    instructions = ""
    functions = tuple()
    agents = tuple()
    model = "gpt-4o-mini"


def agent_to_dict(agent: BaseAgent) -> dict:
    """Convert agent instance to dictionary."""
    agent_name = agent.name if agent.name else agent.__name__
    tools = [get_function_schema(tool) for tool in agent.functions]
    for subagent in agent.agents:
        subagent_name = subagent.name if subagent.name else subagent.__name__
        tools.append(
            get_function_schema(
                FunctionSchema(
                    name=f"transfer_to_{subagent_name}",
                    description=subagent.__doc__,
                )
            )
        )
    return {
        "name": agent_name,
        "instructions": agent.instructions,
        "tools": tools,
        "model": agent.model,
    }


def get_agent_id(agent: BaseAgent) -> str:
    """Get the agent ID.

    We want to have id that is unique to the agent, but does not change
    between runs.
    """
    return hashlib.md5(json.dumps(agent_to_dict(agent)).encode()).hexdigest()


def configure(client: OpenAI, agents: Iterator[BaseAgent]) -> None:
    """Configure all agents.

    Make sure that all agents provided are correctly configured and
    available for use.
    """
    existing_agents = {}
    for agent in client.beta.assistants.list():
        if agent.metadata.get("agent_id") is None:
            client.beta.assistants.delete(agent.id)
        else:
            existing_agents[agent.metadata["agent_id"]] = agent
    for agent in agents:
        agent_id = get_agent_id(agent)
        if agent_id not in existing_agents:
            kwargs = agent_to_dict(agent)
            kwargs["metadata"] = {"agent_id": agent_id}
            log.info("Creating agent %s", kwargs["name"])
            client.beta.assistants.create(**kwargs)
        else:
            log.info("Agent %s exists", agent.name)
            existing_agents.pop(agent_id)
    for agent in existing_agents.values():
        log.info("Deleting agent %s", agent.name)
        client.beta.assistants.delete(agent.id)
    return list(client.beta.assistants.list())


class ArgumentType(enum.StrEnum):
    """Argument type supported for function parameter."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    OBJECT = "object"
    ARRAY = "array"
    ANYOF = "anyOf"


class FunctionParameter(pydantic.BaseModel):
    """Definition of function parameter."""

    name: str = pydantic.Field(description="Name of the parameter")
    type: ArgumentType
    description: str
    required: bool = True
    choices: Optional[list[str]] = None


class FunctionSchema(pydantic.BaseModel):
    """Definition of function schema."""

    name: str = pydantic.Field(description="Name of the function")
    description: str = pydantic.Field(description="Description of the function")
    parameters: list[FunctionParameter] = pydantic.Field(
        default_factory=list, description="List of parameters for the function"
    )


def get_function_schema(my_schema: FunctionSchema) -> str:
    """Return openai compliant function schema."""
    my_data = my_schema.model_dump(exclude_none=True)
    full_param = {
        "type": "object",
        "additionalProperties": False,
        "required": [],
        "properties": {},
    }
    for param in my_data.get("parameters", []):
        full_param["required"].append(param["name"])
        full_param["properties"][param["name"]] = {
            "type": param["type"] if param["required"] else [param["type"], "null"],
            "description": param["description"],
        }
        if "choices" in param:
            full_param["properties"][param["name"]]["enum"] = param["choices"]
    return {
        "type": "function",
        "function": {
            "name": my_data["name"],
            "description": my_data["description"],
            "strict": True,
            "parameters": full_param,
        },
    }


def build_parameter(
    name: str, type: str, description: str, required: bool = True
) -> dict:
    """Build a parameter for openai function."""
    return {
        "name": name,
        "type": type,
        "description": description,
        "required": required,
    }


class StreamHandler(AssistantEventHandler):
    """Handles the stream from openai."""

    def __init__(
        self,
        client: OpenAI,
        thread_id: str,
        assistant_map: dict,
        package: zoozl.chatbot.Package,
        context: zoozl.chatbot.InterfaceRoot,
    ):
        """Initialize the handler with callback."""
        super().__init__()
        self.package = package
        self.client = client
        self.thread_id = thread_id
        self.assistant_map = assistant_map
        self.context = context

    def on_text_done(self, text):
        """Send text back to caller."""
        value = text.value
        for a in text.annotations:
            value = value.replace(a.text, "")
        self.package.callback(value)

    def on_timeout(self):
        """Handle timeout."""
        self.package.callback(
            "I'm sorry, looks like I am daydreaming. Can you repeat that?"
        )
        super().on_timeout()

    def on_tool_call_created(self, tool_call):
        """Receive tool call."""
        log.warning("We received unhandled tool call %s", tool_call)
