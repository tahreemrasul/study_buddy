from google.adk.agents import Agent
from study_guide.config.config import MODEL
from . import prompt

question_answer_agent = Agent(
    name="question_answer_agent",
    model=MODEL,
    description=(
        "responsible for creating question-answer "
        "pairs from study guide "
    ),
    instruction=prompt.QUESTION_ANSWER_PROMPT,
    output_key="question_answer"
)