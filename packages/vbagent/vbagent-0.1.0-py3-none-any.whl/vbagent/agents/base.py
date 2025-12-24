"""Base agent utilities using OpenAI Agents SDK."""

import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

# Lazy import for heavy agents SDK - only import at runtime when needed
if TYPE_CHECKING:
    from agents import Agent, ModelSettings

from vbagent.config import get_model, get_model_settings


def _get_agent_class():
    """Lazy import of Agent class."""
    from agents import Agent
    return Agent


def _get_runner_class():
    """Lazy import of Runner class."""
    from agents import Runner
    return Runner


def _get_model_settings_class():
    """Lazy import of ModelSettings class."""
    from agents import ModelSettings
    return ModelSettings


def encode_image(image_path: str) -> tuple[str, str]:
    """Encode an image file to base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (base64_data, media_type)
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    with open(path, "rb") as f:
        image_bytes = f.read()
    
    image_data = base64.b64encode(image_bytes).decode("utf-8")
    
    suffix = path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    
    return image_data, media_type


def create_image_message(image_path: str, text: str) -> list[dict[str, Any]]:
    """Create a message with image and text for the agent.
    
    Uses the OpenAI Responses API format for image input.
    
    Args:
        image_path: Path to the image file
        text: Text message to accompany the image
        
    Returns:
        List containing a single message dict in Responses API format
    """
    image_data, media_type = encode_image(image_path)
    # Responses API format: message with content list containing input_image and input_text
    return [
        {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:{media_type};base64,{image_data}",
                    "detail": "auto"
                },
                {"type": "input_text", "text": text}
            ]
        }
    ]


def create_agent(
    name: str,
    instructions: str,
    model: Optional[str] = None,
    model_settings: Optional["ModelSettings"] = None,
    output_type: Optional[type] = None,
    tools: Optional[list] = None,
    agent_type: Optional[str] = None,
) -> "Agent":
    """Create an agent with default configuration.
    
    Args:
        name: Agent name
        instructions: System prompt / instructions
        model: Model to use (if None, uses config for agent_type)
        model_settings: Optional ModelSettings for temperature, max_tokens, etc.
        output_type: Optional Pydantic model for structured output
        tools: Optional list of tools (@function_tool decorated functions)
        agent_type: Agent type for config lookup (classifier, scanner, tikz, etc.)
        
    Returns:
        Configured Agent instance
    """
    Agent = _get_agent_class()
    
    # Get model and settings from config if not explicitly provided
    if model is None:
        model = get_model(agent_type or "default")
    if model_settings is None:
        model_settings = get_model_settings(agent_type or "default")
    
    return Agent(
        name=name,
        instructions=instructions,
        model=model,
        model_settings=model_settings,
        output_type=output_type,
        tools=tools or [],
    )


def _print_agent_info(agent: "Agent") -> None:
    """Print agent information when running.
    
    Args:
        agent: The Agent instance being run
    """
    model = agent.model or "default"
    reasoning = "unknown"
    
    # Extract reasoning effort from model_settings if available
    if agent.model_settings:
        settings = agent.model_settings
        if hasattr(settings, 'reasoning') and settings.reasoning:
            reasoning_obj = settings.reasoning
            # Handle both dict and Reasoning object
            if isinstance(reasoning_obj, dict):
                reasoning = reasoning_obj.get('effort', 'unknown')
            elif hasattr(reasoning_obj, 'effort'):
                reasoning = reasoning_obj.effort or 'unknown'
    
    # Use dim styling for subtle output
    print(f"\033[2m⚡ {agent.name} | model: {model} | reasoning: {reasoning}\033[0m")


async def run_agent(agent: "Agent", input_text: str | list) -> Any:
    """Run an agent asynchronously and return the final output.
    
    Args:
        agent: The Agent instance to run
        input_text: The input text or message (can be string or list for images)
        
    Returns:
        The agent's final output (string or structured type)
    """
    Runner = _get_runner_class()
    _print_agent_info(agent)
    result = await Runner.run(agent, input=input_text)
    return result.final_output


def run_agent_sync(agent: "Agent", input_text: str | list) -> Any:
    """Run an agent synchronously and return the final output.
    
    Uses a thread to allow immediate Ctrl+C interruption.
    
    Args:
        agent: The Agent instance to run
        input_text: The input text or message (can be string or list for images)
        
    Returns:
        The agent's final output (string or structured type)
        
    Raises:
        KeyboardInterrupt: If user presses Ctrl+C
    """
    import concurrent.futures
    import threading
    
    Runner = _get_runner_class()
    _print_agent_info(agent)
    
    # Use a thread pool to run the agent, allowing Ctrl+C to interrupt
    result_holder = {"result": None, "error": None}
    
    def run_in_thread():
        try:
            result_holder["result"] = Runner.run_sync(agent, input=input_text)
        except Exception as e:
            result_holder["error"] = e
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    
    # Wait for thread with small intervals to allow Ctrl+C handling
    while thread.is_alive():
        thread.join(timeout=0.1)  # Check every 100ms for interrupt
    
    if result_holder["error"]:
        raise result_holder["error"]
    
    return result_holder["result"].final_output
