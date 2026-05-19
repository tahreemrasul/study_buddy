from google.adk.agents import Agent
from study_guide.config.config import MODEL
from . import prompt

outline_agent = Agent(
    name="outline_agent",
    model=MODEL,
    description=(
        "responsible for creating a structured, "
        "high-level outline for a study guide based on a given topic"
        " and/or supplemental material."
    ),
    instruction=prompt.OUTLINE_PROMPT,
    output_key="outline"
)