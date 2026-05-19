from google.adk.agents import LlmAgent

from . import prompt
from google.adk.tools.agent_tool import AgentTool
from .sub_agents.outline import outline_agent
from .sub_agents.search_query import search_query_agent
from .sub_agents.search import search_agent
from .sub_agents.study_guide import study_guide_agent
from .sub_agents.question_answer import question_answer_agent
from study_guide.config.config import MODEL
from .sub_agents.topic_overview.agent import topic_overview_agent

study_guide = LlmAgent(
    name="study_guide",
    model=MODEL,
    description=(
        "manager study_guide_parent to delegate tasks to other agents, "
        "responsible for creating a structured, detailed "
        "study guide on a given topic based on search results and an outlines"
    ),
    instruction=prompt.ORCHESTRATOR_PROMPT,
    tools=[AgentTool(agent=topic_overview_agent),
           AgentTool(agent=search_query_agent),
           AgentTool(agent=search_agent),
           AgentTool(agent=outline_agent),
           AgentTool(agent=study_guide_agent),
           AgentTool(agent=question_answer_agent)]
)

root_agent = study_guide