from google.adk.agents import Agent
from study_guide.config.config import MODEL
from . import prompt

search_query_agent = Agent(
    model=MODEL,
    name="search_query_agent",
    description="responsible for generating search queries"
                "for conducting search on a particular topic",
    output_key="search_queries",
    instruction=prompt.SEARCH_QUERY_PROMPT,
)