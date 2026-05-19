from google.adk.agents import Agent
from study_guide.config.config import MODEL
from . import prompt

study_guide_agent = Agent(
    name="study_guide_agent",
    model=MODEL,
    description=(
        "Responsible for creating a detailed, study guide on topic provided "
        "by user based on search material and outline"
    ),
    instruction=prompt.STUDY_GUIDE_PROMPT,
    output_key="study_guide"
)