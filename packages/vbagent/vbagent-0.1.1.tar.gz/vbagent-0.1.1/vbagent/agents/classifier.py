"""Classifier agent for physics question image classification.

Uses openai-agents SDK to analyze physics question images and extract
structured metadata including question type, difficulty, topic, etc.
"""

from vbagent.agents.base import (
    create_agent,
    create_image_message,
    run_agent_sync,
)
from vbagent.models.classification import ClassificationResult
from vbagent.prompts.classifier import SYSTEM_PROMPT, USER_TEMPLATE


# Create the classifier agent with structured output
classifier_agent = create_agent(
    name="Classifier",
    instructions=SYSTEM_PROMPT,
    output_type=ClassificationResult,
    agent_type="classifier",
)


def classify(image_path: str) -> ClassificationResult:
    """Analyze a physics question image and return structured metadata.
    
    Args:
        image_path: Path to the image file to classify
        
    Returns:
        ClassificationResult with extracted metadata
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
    """
    message = create_image_message(image_path, USER_TEMPLATE)
    result = run_agent_sync(classifier_agent, message)
    return result
