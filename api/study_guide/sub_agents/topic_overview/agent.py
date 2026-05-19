from google.adk.agents import Agent
from study_guide.config.config import MODEL
from . import prompt

topic_overview_agent = Agent(
    name="topic_overview_agent",
    model=MODEL,
    description=(
        "responsible for creating a brief, "
        "concise and coherent overview of the topic provided"
    ),
    instruction=prompt.TOPIC_OVERVIEW_PROMPT,
    output_key="topic_overview"
)