"""Build workshop/study_buddy_workshop.ipynb from the repo's prompts.

Run from anywhere:  python workshop/assets/build_notebook.py
Diagrams: edit diagrams.html, then `node render.js <dir containing node_modules/playwright-core>`.
"""
import pathlib
import runpy

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
# Images are served from GitHub so they render in Colab (Colab ignores cell attachments)
IMG_BASE = "https://raw.githubusercontent.com/tahreemrasul/study_buddy/main/workshop/images"
AG = REPO / "api/study_guide"


# ---------------------------------------------------------------- prompts from the repo
def load(rel, name):
    return runpy.run_path(str(AG / rel))[name]


P = {
    "ORCHESTRATOR_PROMPT": load("prompt.py", "ORCHESTRATOR_PROMPT"),
    "TOPIC_OVERVIEW_PROMPT": load("sub_agents/topic_overview/prompt.py", "TOPIC_OVERVIEW_PROMPT"),
    "SEARCH_QUERY_PROMPT": load("sub_agents/search_query/prompt.py", "SEARCH_QUERY_PROMPT"),
    "SEARCH_PROMPT": load("sub_agents/search/prompt.py", "SEARCH_PROMPT"),
    "OUTLINE_PROMPT": load("sub_agents/outline/prompt.py", "OUTLINE_PROMPT"),
    "STUDY_GUIDE_PROMPT": load("sub_agents/study_guide/prompt.py", "STUDY_GUIDE_PROMPT"),
    "QUESTION_ANSWER_PROMPT": load("sub_agents/question_answer/prompt.py", "QUESTION_ANSWER_PROMPT"),
}

# The repo prompts already contain the PDF grounding lines. The notebook adds grounding in
# section 7, so strip those lines here to get the "before" versions used in sections 2-6.
SRC = ("Source Material (optional, extracted from a document uploaded by the user; empty if none was uploaded):\n"
       "{source_material?}\n")
REPO_INSERTS = {
    "TOPIC_OVERVIEW_PROMPT": [
        ("Topic: The topic of the study guide.\n", SRC),
        ("This will help the user get a high-level understanding of the topic.\n",
         "If Source Material is present, base the overview on it so it reflects what the document actually covers.\n"),
    ],
    "SEARCH_QUERY_PROMPT": [
        ("Topic Overview: A high-level summary describing the subject the study guide will cover.\n", SRC),
        ("Each query should target a distinct subarea, angle, or key concept needed to understand the topic in depth.\n",
         "If Source Material is present, the document is the main source. Target background or concepts the document assumes but does not explain, instead of repeating what it already covers.\n"),
    ],
    "OUTLINE_PROMPT": [
        ("Search Results: Curated content retrieved from sources like Wikipedia, PubMed, or ArXiv based on the topic overview.\n", SRC),
        ("This outline will form the backbone of a detailed study guide in the next steps, so it should capture all the themes and concepts.\n",
         "If Source Material is present, follow the document's structure and cover all of its main concepts. Add sections based on Search Results only when they are needed to understand the document.\n"),
    ],
    "STUDY_GUIDE_PROMPT": [
        ("Outline: \nA structured list of headings and subtopics to organize the study guide. Each heading includes a one-line description of what it should cover.\n", SRC),
        ("Your primary responsibility is to generate a study guide using both your internal knowledge and the provided materials, with the following logic:\n",
         "\n0. If Source Material is present, it is the primary source and takes priority over rules 1 and 2. Base the study guide on the document, keep its terminology and facts, and do not contradict it. Use Search Results and internal knowledge only to add background or fill gaps the document leaves.\n"),
        ("Provide all resources from the search results in a Resources section at the end.",
         " If Source Material is present, list the uploaded document ({source_name?}) first."),
    ],
}
ORCH_ANCHOR = "Prompt them to optionally upload a supplemental document (e.g., lecture notes or research paper as a pdf).\n"
ORCH_SOURCE = ("\nSource Document:\n{source_note?}\nIf a source document is attached, sub-agents read it from shared state. "
               "Only pass them the topic and the outputs of previous steps, as described below.\n")

BASE = dict(P)
for name, edits in REPO_INSERTS.items():
    s = BASE[name]
    for anchor, add in edits:
        assert (anchor + add) in s, (name, anchor[:40])
        s = s.replace(anchor + add, anchor)
    BASE[name] = s
assert ORCH_ANCHOR + ORCH_SOURCE in BASE["ORCHESTRATOR_PROMPT"]
BASE["ORCHESTRATOR_PROMPT"] = BASE["ORCHESTRATOR_PROMPT"].replace(ORCH_ANCHOR + ORCH_SOURCE, ORCH_ANCHOR)


def py_str(name, text):
    assert '"""' not in text and "\\" not in text
    return f'{name} = """{text}"""'


# ---------------------------------------------------------------- cell helpers
cells = []


def md(text):
    cells.append(new_markdown_cell(text.strip("\n")))


def img(name, alt):
    return f"![{alt}]({IMG_BASE}/{name}.png)"


def code(text, form=False):
    c = new_code_cell(text.strip("\n"))
    if form:
        c["metadata"]["cellView"] = "form"
    cells.append(c)


def solution(text):
    code("#@title Solution\n" + text.strip("\n"), form=True)


# =============================================================================
md(f"""
# Build a NotebookLM-style study guide generator with Gemini and ADK

**DevFest Hamburg 2026 · hands-on workshop, 105 minutes**

Today we're building Study Buddy. You give it a topic, or your own PDF, and a handful of agents research it, outline it, write a study guide and turn that into practice questions.

{img("app_progress", "Study Buddy app")}

That's the finished app. Everything we write in this notebook is its backend. The frontend code is in the [GitHub repo](https://github.com/tahreemrasul/study_buddy) if you want to run the whole thing later.

**What we'll cover**
- splitting a GenAI task into several small steps instead of one big prompt
- the main ADK pieces: agents, tools, sessions, state and events
- grounding the output in a document the user uploads
- when you actually need an LLM to orchestrate, and when a fixed sequence does the job
- serving the agents as an API that a frontend can call

**What you need:** a Google account for Colab, and a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). The free tier is enough.
""")

md(f"""
## How the app fits together

{img("d_architecture", "Study Buddy architecture")}

The app runs as three processes: a Next.js frontend, a small FastAPI proxy, and an ADK server that runs the agents. We'll spend most of the session on the agents. Near the end we'll start them with `adk api_server`, which is how the real app runs them, and then look at what the frontend does with the results.

{img("d_roadmap", "Build order")}

| Section | Time |
|---|---|
| 0 · Setup | 10 min |
| 1 · The root agent | 12 min |
| 2 · Topic overview | 10 min |
| 3 · Research | 12 min |
| 4 · Outline and study guide | 10 min |
| 5 · Practice questions | 8 min |
| 6 · The full pipeline | 10 min |
| 7 · Using your own PDF | 15 min |
| Checkpoint · do we need the orchestrator? | 8 min |
| 8 · Running it as a backend | 10 min |

Each section has an exercise. The solution sits in a collapsed cell underneath; double-click it if you get stuck.
""")

# =============================================================================
md("""
---
# 0 · Setup

### 0.1 Install the libraries
`google-adk` is the Agent Development Kit and `google-genai` is the Gemini SDK it uses. `pypdf` reads PDFs (section 7), and `arxiv` and `wikipedia` are what the search agent will use. The versions match the repo.

If Colab asks you to restart the session after the install, do that and carry on from the next cell.
""")
code("""
!pip install -q google-adk==1.10.0 google-genai==1.29.0 pypdf==6.20.1 arxiv==2.2.0 wikipedia==1.4.0
""")

md("""
### 0.2 Add your API key
Create a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Then in Colab, open the key icon in the left sidebar, add a secret called `GEMINI_API_KEY`, paste the key in, and turn on notebook access. That way the key never ends up in the notebook itself.

Setting `GOOGLE_GENAI_USE_VERTEXAI=FALSE` makes the SDK use the Gemini API with your key, rather than Vertex AI on Google Cloud.
""")
code("""
import os

try:
    from google.colab import userdata
    os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
except ImportError:
    pass  # not in Colab: set GEMINI_API_KEY in your environment instead

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
assert os.environ.get("GEMINI_API_KEY"), "Add GEMINI_API_KEY to Colab Secrets (key icon on the left)"
print("API key loaded")
""")

md("""
### 0.3 Check the key works
We'll use `gemini-3.8-flash` everywhere. Before bringing ADK in, one plain call with the Gemini SDK to make sure the key is fine.
""")
code("""
import logging
from google import genai

# Hides an SDK notice about "non-text parts" (Gemini's internal thought signatures)
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

MODEL_NAME = "gemini-3.8-flash"

client = genai.Client()
response = client.models.generate_content(model=MODEL_NAME, contents="In one sentence: what is a study guide?")
print(response.text)
""")

md("""
### 0.4 Handle rate limits
Free-tier keys have a per-minute limit. The full pipeline makes a dozen or more model calls in a couple of minutes, which is enough to hit it, and when that happens the API returns `429 RESOURCE_EXHAUSTED`.

Instead of letting that crash a run, we tell ADK to wait and retry: 5 seconds, then 10, 20 and so on up to a minute, at most 8 tries. Every agent in the notebook shares this `MODEL`. If a cell seems to hang for a while later on, it's probably waiting out the limit.
""")
code("""
from google.adk.models.google_llm import Gemini
from google.genai import types

MODEL = Gemini(
    model=MODEL_NAME,
    retry_options=types.HttpRetryOptions(attempts=8, initial_delay=5, max_delay=60, exp_base=2),
)
""")

# =============================================================================
md(f"""
---
# 1 · The root agent

Every ADK app has a root agent. It's the one that receives the user's message. We'll start with the simplest version that could work, a single agent told to write a study guide, and build out from there.

First, what ADK actually does when it runs an agent.

{img("d_adk", "How ADK runs an agent")}

**Agent.** An `LlmAgent` is a model plus an instruction (its system prompt), and optionally some tools. Each time it's called, the model either replies with text or asks to call one of its tools.

**Runner.** The runner takes one user message and runs the agent until it's done. It builds the prompt from the instruction and the conversation so far, calls the model, runs whatever tool the model asked for, gives the result back to the model, and repeats until the model gives a final answer.

**Session.** A session is one conversation between a user and an app. It has an id, a list of everything that has happened (the events), and a state dictionary. A `SessionService` stores sessions. We'll use `InMemorySessionService`, which keeps them in memory and loses them when the notebook restarts. ADK also has database and Vertex AI versions for production.

**Event.** Every step of a run is recorded as an event: the user's message, a model reply, a tool call, a tool result. Each event has an `author` (the user or an agent's name), its `content`, and `actions`. One of those actions is `state_delta`, which lists any changes the step made to state. `event.is_final_response()` tells you when the agent has finished.

**State.** State is a dictionary that belongs to the session, and every agent in the session can see it. It's how we'll pass data between agents in this notebook:
- an agent writes its answer into state with `output_key="some_key"`,
- an instruction reads a value back with a placeholder like `{{some_key}}`, which ADK fills in before calling the model,
- you can also put values into state yourself when you create the session.

Keys can have a prefix that changes how long they live: `user:` keys follow the user across sessions, `app:` keys are shared by everyone using the app, and `temp:` keys only last for the current run. We only need plain keys today.

Keep two things in mind: state is how agents share data, and events are what the frontend listens to.
""")

md("""
### 1.1 A helper for running agents in Colab
In the real app we never touch the runner ourselves. `adk api_server` creates sessions and runs agents whenever the frontend sends a request, and we'll use it in section 8. Here in Colab there's no server, so we run agents directly from Python.

This helper is only for the notebook; it isn't part of the app. It does what the server would do: create a session, run one message through a `Runner`, and print each event so we can watch the agent work.
""")
code('''
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME = "study_guide"
USER_ID = "student"

session_service = InMemorySessionService()  # sessions live in memory (adk api_server does the same by default)


def show_event(event):
    """Print a short line for each thing that happened in one event."""
    for part in (event.content.parts if event.content else None) or []:
        if part.function_call:  # the model asked to call a tool or a sub-agent
            print(f"[{event.author}] calls {part.function_call.name} {str(part.function_call.args)[:100]}")
        elif part.function_response:  # the tool's result is going back to the model
            print(f"[{event.author}] got the result of {part.function_response.name}")
        elif part.text:  # an ordinary text reply
            print(f"[{event.author}] says: {part.text[:150]!r}")
    if event.actions.state_delta:  # this step saved something to state
        print(f"[{event.author}] saved to state: {list(event.actions.state_delta)}")


async def run_agent(agent, message, state=None, verbose=True):
    """Run `agent` on one message in a new session. Returns (final reply, session)."""
    # 1. Start a new session. `state` lets us put values in before the agent runs (we use this in section 7).
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state=state or {})

    # 2. The runner executes the agent and yields events as they happen.
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    user_message = types.Content(role="user", parts=[types.Part(text=message)])

    reply = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=user_message):
        if verbose:
            show_event(event)
        if event.is_final_response():  # the agent's last answer
            reply = event.content.parts[0].text if event.content and event.content.parts else ""

    # 3. Fetch the session again so we get the final state and every event.
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session.id)
    return reply, session
''')

md("""
### 1.2 The simplest root agent
An `LlmAgent` needs three things: a name, a model and an instruction.
""")
code('''
from google.adk.agents import LlmAgent
from IPython.display import Markdown, display

naive_root = LlmAgent(
    name="study_guide",
    model=MODEL,
    instruction="You create study guides. Write a concise study guide in Markdown on the topic the user gives you.",
)

guide, session = await run_agent(naive_root, "photosynthesis")
display(Markdown(guide[:2500]))
''')

md(f"""
### 1.3 Is that good enough?
It reads well. But compare it with what we want from a NotebookLM-style tool.

{img("d_monolith", "One agent vs several")}

Everything in that guide came from the model's memory. That's fine for photosynthesis, but for a niche topic it will fill gaps with guesses. It also can't use your lecture notes. The frontend has nothing to show while it works, just one long wait and then a wall of text. And the outline and the questions aren't separate pieces we could display or regenerate on their own.

So we'll split the job up. Each step gets its own small agent with a short, focused prompt, and the root agent's job becomes calling them in the right order. The rest of the notebook builds those sub-agents one at a time.
""")

# =============================================================================
md(f"""
---
# 2 · Sub-agent 1: topic overview

{img("a_topic_overview_agent", "topic_overview_agent")}

The first sub-agent writes a short paragraph introducing the topic. The query planner in the next section uses it to decide what to search for.

Two settings on this agent are new:
- `description` tells other agents what this one does. The root agent reads it when it decides which sub-agent to call.
- `output_key` is the state idea from section 1 in action. Whatever the agent answers gets saved to `state["topic_overview"]`, so later agents (and the frontend) can pick it up.

This is the prompt from the app:
""")
code(py_str("TOPIC_OVERVIEW_PROMPT", BASE["TOPIC_OVERVIEW_PROMPT"]))
code('''
topic_overview_agent = LlmAgent(
    name="topic_overview_agent",
    model=MODEL,
    description="responsible for creating a brief, concise and coherent overview of the topic provided",
    instruction=TOPIC_OVERVIEW_PROMPT,
    output_key="topic_overview",  # the reply is saved to state["topic_overview"]
)

overview, session = await run_agent(topic_overview_agent, "photosynthesis")
print("\\nState now has:", list(session.state))
''')

md(f"""
The last line of the log says `saved to state: ['topic_overview']`. That's `output_key` doing its job.

### 2.1 Connecting it to the root agent
There are two ways to connect agents in ADK.

{img("d_agenttool", "AgentTool vs sub_agents")}

We use `AgentTool`. It wraps the sub-agent so the root agent can call it like any other tool: it sends a request, gets the answer back, and stays in charge of what happens next. With `sub_agents`, the root would hand the whole conversation over to the child, which suits routing (say, sending billing questions to a billing agent) but not a fixed pipeline like ours.
""")
code('''
from google.adk.tools.agent_tool import AgentTool

root_v2 = LlmAgent(
    name="study_guide",
    model=MODEL,
    instruction=(
        "You help users create study guides. When the user gives a topic, call topic_overview_agent "
        "with the topic and present the overview under the heading 'Topic Overview for [Topic]'."
    ),
    tools=[AgentTool(agent=topic_overview_agent)],  # the sub-agent becomes a tool
)

_, session = await run_agent(root_v2, "black holes")
print("\\nState now has:", list(session.state))
''')

md("""
Read the log from the top:
1. `[study_guide] calls topic_overview_agent {'request': ...}`. The root agent decided to use its tool, and the only argument is a `request` string. That string is all the sub-agent sees of the conversation. This becomes important in section 7.
2. `got the result of topic_overview_agent`. The answer came back to the root.
3. `saved to state: ['topic_overview']`. The sub-agent's `output_key` was copied into the root's session state.
4. The root agent presents the overview.

### Exercise 2.1 · Read from state (6 min)
We've seen agents write to state. Now make one read from it. Build an overview agent whose audience comes from state instead of being written into the prompt:

1. Add a line like `Write the overview for this audience: {audience}` to the end of `TOPIC_OVERVIEW_PROMPT`.
2. Run the agent twice on the same topic, passing `state={"audience": "a 12-year-old"}` and then `state={"audience": "a PhD student in plant biology"}`. One agent, two very different answers.
3. Now run it without passing any state. What happens? Then change the placeholder to `{audience?}` and try again.

Part 3 is the reason section 7 works, so don't skip it.
""")
code('''
# Your code here
''')
solution('''
audience_agent = LlmAgent(
    name="topic_overview_agent",
    model=MODEL,
    instruction=TOPIC_OVERVIEW_PROMPT + "\\nWrite the overview for this audience: {audience}\\n",
)

# 1-2. Same agent, different value in state
for audience in ["a 12-year-old", "a PhD student in plant biology"]:
    reply, _ = await run_agent(audience_agent, "photosynthesis", state={"audience": audience}, verbose=False)
    print(f"--- {audience}\\n{reply}\\n")

# 3. Without the key, ADK can't fill {audience} and raises an error
try:
    await run_agent(audience_agent, "photosynthesis", verbose=False)
except KeyError as error:
    print("Without state:", error)

# With {audience?} the placeholder is optional: it becomes an empty string instead of an error
optional_agent = LlmAgent(
    name="topic_overview_agent",
    model=MODEL,
    instruction=TOPIC_OVERVIEW_PROMPT + "\\nWrite the overview for this audience: {audience?}\\n",
)
reply, _ = await run_agent(optional_agent, "photosynthesis", verbose=False)
print("With {audience?} and no state, it still runs:\\n", reply[:300])
''')

# =============================================================================
md(f"""
---
# 3 · Research: sub-agents 2 and 3

To get past what the model remembers, the app does a little research first. A query planner turns the overview into two search queries, and a search agent runs them against Wikipedia and arXiv.

### 3.1 The query planner

{img("a_search_query_agent", "search_query_agent")}
""")
code(py_str("SEARCH_QUERY_PROMPT", BASE["SEARCH_QUERY_PROMPT"]))
code('''
search_query_agent = LlmAgent(
    name="search_query_agent",
    model=MODEL,
    description="responsible for generating search queries for conducting search on a particular topic",
    instruction=SEARCH_QUERY_PROMPT,
    output_key="search_queries",
)

# For now we act as the orchestrator and pass the overview in ourselves
queries, _ = await run_agent(search_query_agent, f"Topic Overview:\\n{overview}")
print("\\n" + queries)
''')

md(f"""
### 3.2 Tools are just Python functions
Any Python function can be a tool. ADK reads its name, its type hints and its docstring, and passes that description to Gemini. The docstring is what the model reads when it decides whether to use the tool, so it's worth writing a good one.

{img("d_tools", "Functions as tools")}

Here are the two search tools from the app. If a search fails they return a short message telling the model to rely on other sources instead of raising an error, so one broken API doesn't take down the whole run.
""")
code('''
import time
import urllib.request

import arxiv
import wikipedia

# Wikipedia asks API clients to send a User-Agent
opener = urllib.request.build_opener()
opener.addheaders = [("User-Agent", "study-buddy/1.0 (research project)")]
urllib.request.install_opener(opener)


def search_arxiv(query: str) -> list[dict]:
    """Search for relevant publications on arXiv"""
    try:
        results = arxiv.Client().results(arxiv.Search(query=query, max_results=2))
        docs = [{"title": paper.title, "content": paper.summary} for paper in results]
        return docs or [{"content": "No results found on Arxiv. Use internal knowledge."}]
    except Exception:
        return [{"content": "arXiv unavailable. Use Wikipedia and internal knowledge instead."}]


def search_wikipedia(query: str) -> list[dict]:
    """Search for information on Wikipedia"""
    docs = []
    try:
        for title in wikipedia.search(query, results=3):
            try:
                page = wikipedia.page(title, auto_suggest=False)
                docs.append({"title": page.title, "content": page.summary})
            except Exception:  # disambiguation or missing pages: skip them
                continue
    except Exception:  # Wikipedia itself is unreachable
        pass
    return docs or [{"content": "No results found on Wikipedia. Use internal knowledge."}]


# A tool is still a normal function, so we can test it without a model
for doc in search_wikipedia("light-dependent reactions"):
    print("-", doc.get("title"), ":", doc["content"][:100])
''')

md(f"""
### 3.3 The search agent

{img("a_search_agent", "search_agent")}

We pass both functions in `tools`. The prompt explains how to use them, and Gemini picks which one to call for each query.
""")
code(py_str("SEARCH_PROMPT", BASE["SEARCH_PROMPT"]))
code('''
search_agent = LlmAgent(
    name="search_agent",
    model=MODEL,
    description="Responsible for conducting search for a particular topic given a search query",
    instruction=SEARCH_PROMPT,
    tools=[search_arxiv, search_wikipedia],  # plain functions become tools
    output_key="search",
)

search_results, _ = await run_agent(search_agent, f"Search Query List:\\n{queries}")
''')

md("""
The `calls search_wikipedia` and `calls search_arxiv` lines are Gemini choosing a tool and ADK running your function. This is one place where having a model in the loop really helps, because deciding which source suits a query is a judgment call.

### Exercise 3.1 · Write your own tool (8 min)
Wikipedia summaries are short. Give the search agent a way to read a whole article:

1. Write `get_wikipedia_page(title: str) -> dict` that returns the page's title and the first 4,000 characters of `wikipedia.page(title, auto_suggest=False).content`. Return an error message instead of raising if the page can't be loaded.
2. Write a docstring that tells the model when to use it, for example after `search_wikipedia` when a summary is too thin.
3. Build a new search agent with all three tools and run it on `"Calvin cycle enzymes and regulation"`. Does it call your tool? Try a vaguer docstring and see if that changes.
""")
code('''
# Your code here
''')
solution('''
def get_wikipedia_page(title: str) -> dict:
    """Read the full text of one Wikipedia article by its exact title.
    Use this after search_wikipedia when a summary is not detailed enough."""
    try:
        page = wikipedia.page(title, auto_suggest=False)
        return {"title": page.title, "content": page.content[:4000]}
    except Exception as error:
        return {"content": f"Could not load the page ({type(error).__name__})."}


deep_search_agent = LlmAgent(
    name="search_agent",
    model=MODEL,
    instruction=SEARCH_PROMPT + "\\nIf a Wikipedia summary is too short, read the full article with get_wikipedia_page.",
    tools=[search_arxiv, search_wikipedia, get_wikipedia_page],
    output_key="search",
)
await run_agent(deep_search_agent, "Search Query List:\\n1. Calvin cycle enzymes and regulation")
''')

# =============================================================================
md(f"""
---
# 4 · Outline and study guide: sub-agents 4 and 5

Next, an outline agent plans the sections and a study guide agent writes them up. Look at the inputs on these two cards: each needs several earlier results.

{img("a_outline_agent", "outline_agent")}

{img("a_study_guide_agent", "study_guide_agent")}

So far we've been doing the orchestrator's job by hand, pasting earlier results into each message. We'll keep doing that for these two, then hand it over to the root agent in section 6.
""")
code(py_str("OUTLINE_PROMPT", BASE["OUTLINE_PROMPT"]))
code('''
outline_agent = LlmAgent(
    name="outline_agent",
    model=MODEL,
    description=("responsible for creating a structured, high-level outline for a study guide "
                 "based on a given topic and/or supplemental material."),
    instruction=OUTLINE_PROMPT,
    output_key="outline",
)

outline, _ = await run_agent(outline_agent, f"Topic Overview:\\n{overview}\\n\\nSearch Results:\\n{search_results}")
print("\\n" + outline)
''')
code(py_str("STUDY_GUIDE_PROMPT", BASE["STUDY_GUIDE_PROMPT"]))
code('''
study_guide_agent = LlmAgent(
    name="study_guide_agent",
    model=MODEL,
    description=("Responsible for creating a detailed, study guide on topic provided by user "
                 "based on search material and outline"),
    instruction=STUDY_GUIDE_PROMPT,
    output_key="study_guide",
)

study_guide, _ = await run_agent(
    study_guide_agent,
    f"Topic Overview:\\n{overview}\\n\\nSearch Results:\\n{search_results}\\n\\nOutline:\\n{outline}",
    verbose=False,
)
display(Markdown(study_guide[:3000]))
''')

md("""
One line in that prompt is worth copying into your own projects: *"Only list resources that actually appear in the Search Results… Never invent titles, authors or publications."* Without it, models happily fill a Resources section with citations that look real and don't exist.

### Exercise 4.1 · Pass results through state (6 min)
Pasting results into the message works, but it means someone has to build that message. The alternative is to let the agent read its inputs from state:

1. Make `outline_from_state`, a copy of the outline agent whose instruction is `OUTLINE_PROMPT` plus an Inputs section containing `{topic_overview}` and `{search}`.
2. Run it with the message `"Create the outline."` and `state={"topic_overview": overview, "search": search_results}`.

Same output, but nobody had to write the message. Keep this pattern in mind for the checkpoint after section 7.
""")
code('''
# Your code here
''')
solution('''
outline_from_state = LlmAgent(
    name="outline_agent",
    model=MODEL,
    instruction=OUTLINE_PROMPT + "\\nInputs:\\nTopic Overview:\\n{topic_overview}\\n\\nSearch Results:\\n{search}\\n",
    output_key="outline",
)
reply, _ = await run_agent(
    outline_from_state,
    "Create the outline.",
    state={"topic_overview": overview, "search": search_results},
    verbose=False,
)
print(reply)
''')

# =============================================================================
md(f"""
---
# 5 · Practice questions as JSON: sub-agent 6

{img("a_question_answer_agent", "question_answer_agent")}

The last sub-agent turns the guide into practice questions. This output is different from the others, because code reads it: the frontend turns it into flashcards. So the prompt asks for JSON with a difficulty level on each question.
""")
code(py_str("QUESTION_ANSWER_PROMPT", BASE["QUESTION_ANSWER_PROMPT"]))
code('''
import json

question_answer_agent = LlmAgent(
    name="question_answer_agent",
    model=MODEL,
    description="responsible for creating question-answer pairs from study guide",
    instruction=QUESTION_ANSWER_PROMPT,
    output_key="question_answer",
)

qa_raw, _ = await run_agent(question_answer_agent, f"Study Guide:\\n{study_guide}", verbose=False)


def parse_qa(raw):
    """Turn the model's reply into a list of questions (the frontend does the same thing)."""
    text = raw.replace("```json", "").replace("```", "").strip()  # the model often wraps JSON in a code block
    data = json.loads(text)
    if isinstance(data, dict):  # sometimes it's {"questions": [...]} instead of a plain list
        data = next(iter(data.values()))
    return data


questions = parse_qa(qa_raw)
for q in questions[:5]:
    print(f"[{q['difficulty']}] {q['question']}")
print(f"... {len(questions)} questions in total")
''')

md("""
`parse_qa` has to strip code fences and guess at the shape of the reply. The model gets it right most of the time, but "most of the time" isn't great for code that drives a UI.

### Exercise 5.1 · Structured output (8 min)
ADK can make the model return a fixed shape. Pass a Pydantic class as `output_schema` and Gemini's reply has to match it.

1. Define `QAPair` with `question`, `answer` and `difficulty` (one of "Easy", "Medium", "Hard"), and `QASet` with a list of `QAPair`.
2. Build `qa_structured_agent` with `output_schema=QASet` and run it on `study_guide`.
3. Load the reply with `QASet.model_validate_json(...)`. No fence-stripping or guessing needed.

An agent with `output_schema` can't use tools, which is fine here.
""")
code('''
# Your code here
''')
solution('''
from typing import Literal
from pydantic import BaseModel


class QAPair(BaseModel):
    question: str
    answer: str
    difficulty: Literal["Easy", "Medium", "Hard"]


class QASet(BaseModel):
    questions: list[QAPair]


qa_structured_agent = LlmAgent(
    name="question_answer_agent",
    model=MODEL,
    instruction=QUESTION_ANSWER_PROMPT,
    output_schema=QASet,  # the reply must match this shape
    output_key="question_answer",
)
reply, _ = await run_agent(qa_structured_agent, f"Study Guide:\\n{study_guide}", verbose=False)
qa_set = QASet.model_validate_json(reply)
print(len(qa_set.questions), "questions. First one:", qa_set.questions[0].question)
''')

# =============================================================================
md(f"""
---
# 6 · The full pipeline

Up to now we've passed results from one agent to the next ourselves. Now the root agent takes over that job. It gets all six sub-agents as tools and an instruction that describes the workflow.

{img("d_pipeline", "The full pipeline")}

This is the orchestrator prompt from the app. The Workflow part has one block per sub-agent, saying what to send it and what to do with the answer, and it tells the agent to keep going without waiting for the user between steps.
""")
code(py_str("ORCHESTRATOR_PROMPT", BASE["ORCHESTRATOR_PROMPT"]))
code('''
root_agent = LlmAgent(
    name="study_guide",
    model=MODEL,
    description=("manager study_guide_parent to delegate tasks to other agents, responsible for creating a "
                 "structured, detailed study guide on a given topic based on search results and an outlines"),
    instruction=ORCHESTRATOR_PROMPT,
    tools=[
        AgentTool(agent=topic_overview_agent),
        AgentTool(agent=search_query_agent),
        AgentTool(agent=search_agent),
        AgentTool(agent=outline_agent),
        AgentTool(agent=study_guide_agent),
        AgentTool(agent=question_answer_agent),
    ],
)
''')

md("""
### 6.1 Run it
This one makes a lot of model calls and takes two or three minutes. Watch the log: the root calls each sub-agent in turn and the state fills up.
""")
code('''
start = time.time()
_, orchestrated_session = await run_agent(root_agent, "photosynthesis")
print(f"\\nFinished in {time.time() - start:.0f}s")
print("State now has:", list(orchestrated_session.state))
''')
code('''
display(Markdown(orchestrated_session.state["study_guide"]))
''')

md("""
### 6.2 What the frontend sees
Each `calls ..._agent` line in that log is an event the frontend receives too. Its React hook does two things with them. When it sees a call to `outline_agent`, it moves the progress bar to step 4. When an event saves `outline` to state, it fills in the Outline card.

That's why the `output_key` names matter. They're the agreement between the backend and the UI.

### Exercise 6.1 · Add an output (8 min)
The workshop description promised key concepts as well. Write a `key_concepts_agent` that reads a study guide and returns a glossary of 8 to 12 terms with one-line definitions, saved with `output_key="key_concepts"`. Test it on `orchestrated_session.state["study_guide"]`.

To add it to the pipeline you'd put `AgentTool(agent=key_concepts_agent)` in the root agent's tools and add a step for it to the Workflow in `ORCHESTRATOR_PROMPT`. That's another full run, so try it at home.
""")
code('''
# Your code here
''')
solution('''
key_concepts_agent = LlmAgent(
    name="key_concepts_agent",
    model=MODEL,
    description="responsible for extracting a glossary of key concepts from a study guide",
    instruction=(
        "Role: You extract key concepts from a study guide.\\n"
        "Input: Study Guide.\\n"
        "Output: a Markdown list of 8-12 key terms, each with a one-line definition taken from the guide. "
        "Only use terms and facts present in the study guide. Do not use emojis."
    ),
    output_key="key_concepts",
)
concepts, _ = await run_agent(key_concepts_agent, f"Study Guide:\\n{orchestrated_session.state['study_guide']}", verbose=False)
display(Markdown(concepts))
''')

# =============================================================================
md("""
---
# 7 · Using your own PDF

Tools like NotebookLM work from your sources, not just from what the model knows. So let's let the user attach a PDF and build the guide from it.

### 7.1 Where should the PDF go?
Think back to section 2. When the root agent calls a sub-agent through `AgentTool`, the sub-agent only gets the `request` string the root writes. If we attached the PDF to the user's message, the root agent would see it, but the outline and study guide agents, the ones that actually need it, never would.

Here are the options we considered for the app:

| Option | How it works | Trade-off |
|---|---|---|
| Attach the PDF to the user's message | Gemini can read PDFs directly | Only the root agent sees it, and the whole file is re-sent on every one of its model calls |
| Ask Gemini to summarise the PDF first | One extra model call turns it into notes | The agents then work from an AI-written summary, which can drop or change details |
| Extract the text with a parser and put it in state | `pypdf` reads the text, no model involved | Every sub-agent sees the real text, but scanned PDFs (images only) have no text to extract |

We went with the third. Reading a file is a normal preprocessing step, so we don't need an agent for it.
""")
md(f"""
{img("d_grounding", "Getting the PDF to every sub-agent")}

### 7.2 Get a PDF
We'll use a short lecture about Lake Varnholm. The lake doesn't exist and everything in the lecture is made up: the "Brekke layer", the "Varnholm Turnover Index", a fish called *Salvelinus varnholmi*. That makes it a good test. If those details turn up in the study guide, the PDF is the only place they could have come from.
""")
code('''
PDF_PATH = "varnholm_lecture.pdf"
PDF_URL = "https://raw.githubusercontent.com/tahreemrasul/study_buddy/main/workshop/data/varnholm_lecture.pdf"

if not os.path.exists(PDF_PATH):
    urllib.request.urlretrieve(PDF_URL, PDF_PATH)
print("Downloaded", PDF_PATH)
''')

md("""
### 7.3 Turn the PDF into state
`pdf_to_state` reads the PDF and returns a dictionary we'll pass in as the session's starting state. The app's proxy (`api/server.py`) runs the same logic when someone uploads a file.
""")
code('''
from pypdf import PdfReader

MAX_SOURCE_CHARS = 100_000  # the text goes into several prompts, so keep it to a sensible size


def pdf_to_state(path):
    """Read a PDF and return the session state the agents expect."""
    name = os.path.basename(path)

    # Pull the text out of every page. Pages without a text layer (scans) give back None.
    pages = PdfReader(path).pages
    text = "\\n\\n".join(page.extract_text() or "" for page in pages).strip()
    if not text:
        return {"source_error": f"No text found in {name}. Is it a scanned PDF?"}

    return {
        "source_name": name,                          # listed first in the guide's Resources section
        "source_material": text[:MAX_SOURCE_CHARS],   # the text the sub-agents read
        # A note for the root agent, so it knows a document exists without pasting it around
        "source_note": f"The user attached '{name}'. Sub-agents can already read it, so don't paste it into requests. "
                       "If the user gave no topic, use the document's subject as the topic.",
    }


source_state = pdf_to_state(PDF_PATH)
print(source_state["source_material"][:500])
''')

md("""
### 7.4 Teach the sub-agents to use it
The PDF text is in state now, but no prompt mentions it yet. We'll add the same short section to the end of four prompts: the overview, query planner, outline and study guide. The other two don't need it. The search agent just runs whatever queries it's given, and the Q&A agent only reads the study guide, which will already be based on the PDF.

The section has two parts:
1. A **Source Material** input with the placeholder `{source_material?}`. ADK replaces it with the PDF text from state. Because of the `?` (remember exercise 2.1), it becomes an empty string when there's no PDF, so the same prompts work with or without a document.
2. One sentence telling that particular agent what to do with the document.

Nothing in the original prompts gets rewritten. We only add to the end. (In the repo these lines sit inside each prompt file instead, which works the same way.)
""")
code('''
SOURCE_SECTION = """

Source Material (the text of a document the user uploaded; empty if there isn't one):
{source_material?}
"""

GROUNDED_TOPIC_OVERVIEW_PROMPT = TOPIC_OVERVIEW_PROMPT + SOURCE_SECTION + (
    "If Source Material is present, base the overview on it so it reflects what the document actually covers.")

GROUNDED_SEARCH_QUERY_PROMPT = SEARCH_QUERY_PROMPT + SOURCE_SECTION + (
    "If Source Material is present, the document is the main source. Write queries for background the document "
    "assumes but doesn't explain, instead of repeating what it already covers.")

GROUNDED_OUTLINE_PROMPT = OUTLINE_PROMPT + SOURCE_SECTION + (
    "If Source Material is present, follow the document's structure and cover all of its main concepts. "
    "Add sections from the Search Results only when they're needed to understand the document.")

GROUNDED_STUDY_GUIDE_PROMPT = STUDY_GUIDE_PROMPT + SOURCE_SECTION + (
    "If Source Material is present, it is the primary source and takes priority over the rules above. Base the guide "
    "on the document, keep its terminology and facts, and don't contradict it. Use the Search Results only for "
    "background or gaps. In Resources, list the uploaded document ({source_name?}) first.")

# The root agent gets the one-line note instead of the whole document
GROUNDED_ORCHESTRATOR_PROMPT = ORCHESTRATOR_PROMPT + """

Source Document:
{source_note?}
If a document is attached, the sub-agents read it from shared state. Only pass them the topic and the outputs of previous steps.
"""

print(GROUNDED_TOPIC_OVERVIEW_PROMPT)
''')

md("""
Now rebuild those four sub-agents with the new prompts, and a root agent that uses them.
""")
code('''
topic_overview_agent = LlmAgent(
    name="topic_overview_agent", model=MODEL, output_key="topic_overview",
    description="responsible for creating a brief, concise and coherent overview of the topic provided",
    instruction=GROUNDED_TOPIC_OVERVIEW_PROMPT,
)
search_query_agent = LlmAgent(
    name="search_query_agent", model=MODEL, output_key="search_queries",
    description="responsible for generating search queries for conducting search on a particular topic",
    instruction=GROUNDED_SEARCH_QUERY_PROMPT,
)
outline_agent = LlmAgent(
    name="outline_agent", model=MODEL, output_key="outline",
    description="responsible for creating a structured, high-level outline for a study guide",
    instruction=GROUNDED_OUTLINE_PROMPT,
)
study_guide_agent = LlmAgent(
    name="study_guide_agent", model=MODEL, output_key="study_guide",
    description="Responsible for creating a detailed study guide based on search material and outline",
    instruction=GROUNDED_STUDY_GUIDE_PROMPT,
)

grounded_root_agent = LlmAgent(
    name="study_guide",
    model=MODEL,
    description=root_agent.description,
    instruction=GROUNDED_ORCHESTRATOR_PROMPT,
    tools=[AgentTool(agent=a) for a in [topic_overview_agent, search_query_agent, search_agent,
                                        outline_agent, study_guide_agent, question_answer_agent]],
)
''')

md("""
### 7.5 Did it work?
Same overview agent, same message, run twice. The first time the session starts empty; the second time it starts with the PDF in state.
""")
code('''
message = "Create a study guide from the attached document."

print("--- without the PDF")
reply, _ = await run_agent(topic_overview_agent, message, verbose=False)
print(reply[:600])

print("\\n--- with the PDF in state")
reply, _ = await run_agent(topic_overview_agent, message, state=source_state, verbose=False)
print(reply[:600])
''')

md("""
Without the PDF the agent has nothing to go on. With it, the overview is full of details about a lake no model has ever heard of.

### 7.6 The whole pipeline, from the PDF
Same idea with the full root agent. This takes about three minutes, so it's a good time for questions.
""")
code('''
_, grounded_session = await run_agent(grounded_root_agent, message, state=source_state)

guide_text = grounded_session.state["study_guide"]
for fact in ["Brekke", "VTI", "0.35", "2.4 mg/L", "Salvelinus varnholmi"]:
    print("found" if fact in guide_text else "MISSING", "-", fact)
''')
code('''
display(Markdown(guide_text))
''')

md("""
Scroll down to Resources at the end. The PDF is listed first, and there are no made-up citations.

### Exercise 7.1 · Your own document (8 min)
Upload a PDF of your own: lecture notes, a paper, some documentation. Turn it into state with `pdf_to_state`, then:
1. run the overview agent with and without that state and compare,
2. run the outline agent on it too, and check that the sections follow your document.

If `pdf_to_state` returns `source_error`, your PDF is probably scanned. Try a different one.
""")
code('''
# Your code here
''')
solution('''
from google.colab import files

uploaded = files.upload()  # pick a PDF from your computer
my_state = pdf_to_state(next(iter(uploaded)))

if "source_error" in my_state:
    print(my_state["source_error"])
else:
    for label, state in [("without", None), ("with", my_state)]:
        reply, _ = await run_agent(topic_overview_agent, message, state=state, verbose=False)
        print(f"--- overview {label} your PDF\\n{reply[:500]}\\n")

    outline, _ = await run_agent(outline_agent, "Create the outline.", state=my_state, verbose=False)
    print("--- outline\\n" + outline)
''')

# =============================================================================
md(f"""
---
# Checkpoint · Do we need the orchestrator?

Look back at the log from section 6. The six steps always run in the same order, yet the root agent still spends model calls deciding what comes next and re-typing each result to present it. In principle it could also skip a step or stop to ask the user something.

{img("d_sequential", "Who decides the order?")}

ADK has workflow agents for this situation. `SequentialAgent`, `ParallelAgent` and `LoopAgent` run their sub-agents in a fixed pattern without a model making the decisions. With a `SequentialAgent` there's no orchestrator writing requests, so each step reads its inputs from state, exactly the pattern from exercise 4.1. Every value it needs is already there because of `output_key`.
""")
code('''
from google.adk.agents import SequentialAgent


def reads_from_state(agent, inputs=""):
    """Copy a sub-agent and add an Inputs section that pulls earlier results from state.
    (A copy, because an ADK agent can only belong to one parent.)"""
    return LlmAgent(
        name=agent.name,
        model=MODEL,
        instruction=agent.instruction + (f"\\n\\nInputs:\\n{inputs}" if inputs else ""),
        tools=agent.tools,
        output_key=agent.output_key,
    )


sequential_pipeline = SequentialAgent(
    name="study_guide",
    sub_agents=[
        reads_from_state(topic_overview_agent),  # reads the topic from the user's message, so no inputs
        reads_from_state(search_query_agent, "Topic Overview:\\n{topic_overview}"),
        reads_from_state(search_agent, "Search Query List:\\n{search_queries}"),
        reads_from_state(outline_agent, "Topic Overview:\\n{topic_overview}\\n\\nSearch Results:\\n{search}"),
        reads_from_state(study_guide_agent,
                         "Topic Overview:\\n{topic_overview}\\n\\nSearch Results:\\n{search}\\n\\nOutline:\\n{outline}"),
        reads_from_state(question_answer_agent, "Study Guide:\\n{study_guide}"),
    ],
)

_, sequential_session = await run_agent(sequential_pipeline, "photosynthesis")
''')

md("""
Now compare the two runs. We count the model calls the root agent made itself, on top of the work the sub-agents did. In the session's events, those are the replies authored by `study_guide` (the root's name in both versions).
""")
code('''
def root_model_calls(session):
    """Count the root agent's own model replies (tool results don't count)."""
    return sum(1 for event in session.events
               if event.author == "study_guide" and event.content and not event.get_function_responses())


print("Model calls spent on orchestration:")
print("  LLM orchestrator:", root_model_calls(orchestrated_session))
print("  SequentialAgent: ", root_model_calls(sequential_session))
print("Same outputs in state:", set(orchestrated_session.state) == set(sequential_session.state))
''')

md("""
The sequential version spends no calls on orchestration and produces the same outputs. It also avoids the root re-typing the whole study guide and the Q&A JSON in its replies, which costs output tokens.

So which one should you use?
- If the steps are always the same, a `SequentialAgent` is cheaper, predictable, and guaranteed to run every step. For this pipeline it's probably the better choice.
- If the next step depends on the content or on what the user asks ("make it shorter", "just redo the questions"), an LLM orchestrator earns its place. The app keeps one partly for this reason; the end of its prompt handles follow-up requests.
- A mix also works: a fixed pipeline to generate everything, with an LLM agent only for follow-up chat.

A simple way to decide: put a model wherever a decision depends on the content, like choosing a search tool, and use fixed code where it doesn't.
""")

# =============================================================================
md(f"""
---
# 8 · Running it as a backend

So far everything ran inside this notebook through our `run_agent` helper. A web app needs an HTTP API instead, and ADK comes with one. Point `adk api_server` at a folder of agents and it handles sessions, runs the agents and streams events back, which is everything `run_agent` was doing for us.

To be clear about what's what in this section: the server side is all ADK. The code cells below are glue that plays the part of the frontend, making the same HTTP calls the Next.js app makes. You wouldn't write any of it on the backend.

{img("d_endpoints", "The backend API")}

### 8.1 Get the app's agents
The repo's `api/study_guide/` folder holds the same agents we just built, one sub-folder per sub-agent. ADK expects a folder per app with an `agent.py` that defines `root_agent`, so we'll clone the repo and serve that folder as it is.
""")
code('''
if not os.path.exists("study_buddy"):
    !git clone -q https://github.com/tahreemrasul/study_buddy.git

!ls study_buddy/api/study_guide study_buddy/api/study_guide/sub_agents
''')

md("""
### 8.2 Start the server
This starts `adk api_server` in the background on port 8000. It inherits the notebook's environment, so it picks up `GEMINI_API_KEY`. On your own machine you'd just run `adk api_server` in a terminal inside `api/`, which is the first of the three terminals in the repo's README.
""")
code('''
import shutil
import subprocess
import sys

import requests

# Find the adk command that came with google-adk, then start the server in the background
adk = shutil.which("adk") or os.path.join(os.path.dirname(sys.executable), "adk")
server = subprocess.Popen([adk, "api_server", "--port", "8000", "study_buddy/api"],
                          stdout=open("adk_server.log", "w"), stderr=subprocess.STDOUT)

BASE_URL = "http://127.0.0.1:8000"

# Wait until the server answers (it takes a few seconds to start)
for _ in range(60):
    try:
        print("Apps on the server:", requests.get(f"{BASE_URL}/list-apps").json())
        break
    except requests.ConnectionError:
        time.sleep(1)
''')

md("""
### 8.3 Create a session with the PDF in it
`POST /apps/{app}/users/{user}/sessions/{session}` creates a session, and the JSON you send becomes its starting state. That's the `state=` argument we've been passing to `run_agent`, now over HTTP. The app's proxy makes this call after it runs `pdf_to_state` on an upload.
""")
code('''
session_id = f"s_{int(time.time())}"
url = f"{BASE_URL}/apps/study_guide/users/{USER_ID}/sessions/{session_id}"

response = requests.post(url, json=source_state)  # the body becomes the session's state
print("Session state:", list(response.json()["state"]))
''')

md("""
### 8.4 Run the agents and read the stream
`POST /run_sse` takes the user's message and answers with a stream of server-sent events: one line per event, starting with `data: `, followed by the event as JSON. They're the same events we've been printing all along.

The loop below is roughly what the frontend's `useStudySession.ts` does. To save time and quota we stop after the first two sub-agents finish. Closing the connection also stops the run on the server.
""")
code('''
body = {
    "appName": "study_guide",
    "userId": USER_ID,
    "sessionId": session_id,
    "newMessage": {"role": "user", "parts": [{"text": "Create a study guide from the attached document."}]},
}

with requests.post(f"{BASE_URL}/run_sse", json=body, stream=True) as stream:
    for line in stream.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue  # skip the blank lines between events
        event = json.loads(line[len("data: "):])

        # Which sub-agent is being called? The frontend uses this to move the progress bar.
        for part in (event.get("content") or {}).get("parts") or []:
            if "functionCall" in part:
                print("calling", part["functionCall"]["name"])

        # What was saved to state? The frontend uses this to fill in each card.
        saved = (event.get("actions") or {}).get("stateDelta") or {}
        if saved:
            print("saved to state:", list(saved))
        if "search_queries" in saved:
            break  # two sub-agents done, that's enough for the demo
''')

md("""
That's the whole contract between the frontend and the backend:

| Call | What it does |
|---|---|
| `GET /list-apps` | lists the agent apps the server found |
| `POST /apps/{app}/users/{user}/sessions/{id}` | creates a session; the body becomes its state |
| `POST /run_sse` | sends a message and streams back events |

The same calls with `curl`, if you're running the server locally:
```bash
curl localhost:8000/list-apps
curl -X POST localhost:8000/apps/study_guide/users/u1/sessions/s1 -H "Content-Type: application/json" -d '{}'
curl -N -X POST localhost:8000/run_sse -H "Content-Type: application/json" \\
  -d '{"appName":"study_guide","userId":"u1","sessionId":"s1","newMessage":{"role":"user","parts":[{"text":"photosynthesis"}]}}'
```
""")
code('''
server.terminate()  # stop the background server
''')

# =============================================================================
md(f"""
---
# The frontend

The Next.js app is a thin layer over those three calls. The code is in the [repo](https://github.com/tahreemrasul/study_buddy).

{img("app_input", "Topic input with an attached PDF")}

| Repo file | What it does | Where we saw it |
|---|---|---|
| `api/study_guide/` | the agents | sections 1 to 7 |
| `api/server.py` | the proxy. Adds CORS headers (browsers block calls to a different port without them) and runs `pdf_to_state` when a session is created with a PDF | section 7.3 and 8.3 |
| `web/app/hooks/useStudySession.ts` | creates the session, opens `/run_sse`, and turns events into progress steps and cards | section 8.4 |
| `web/app/components/` | the Progress, Study Guide and Q&A tabs; the flashcards render the Q&A JSON | `display(Markdown(...))` and `parse_qa` |

{img("app_guide", "Study guide tab")}

To run the whole app on your laptop, follow the README in the repo. It's three terminals (`adk api_server`, `uvicorn server:app --port 8001` and `npm run dev`), then open `http://localhost:3000`.
""")

md("""
---
# Wrapping up

| What we built | The ADK idea behind it |
|---|---|
| a root agent | `LlmAgent`, `Runner`, sessions and events |
| six sub-agents with one job each | short prompts, `description`, `output_key` and state |
| research with Wikipedia and arXiv | Python functions as tools |
| an orchestrator | `AgentTool`, so agents can call other agents |
| grounding in a user's PDF | starting state plus optional `{placeholders?}` |
| a fixed-order version | `SequentialAgent`, and when to use which |
| a backend API | `adk api_server` with sessions and `/run_sse` |

### Ideas for taking it further
- **Chat with your sources.** A follow-up agent that answers questions using `{source_material?}` and `{study_guide?}`.
- **Citations.** Ask the study guide agent to mark each claim with the section of the document it came from.
- **More than one document.** Keep several sources in state and let the user choose.
- **Audio overview.** Turn the guide into a two-person script and voice it with Gemini text-to-speech.
- **More outputs.** Key concepts (exercise 6.1), revision notes, a timeline. Each one is another sub-agent with its own `output_key`.

### Links
- ADK documentation: [google.github.io/adk-docs](https://google.github.io/adk-docs/)
- Gemini API: [ai.google.dev](https://ai.google.dev/)
- Workshop repo: [github.com/tahreemrasul/study_buddy](https://github.com/tahreemrasul/study_buddy)

Thanks for coming!
""")

# ---------------------------------------------------------------- write
nb = new_notebook(cells=cells)
nb.metadata = {
    "colab": {"provenance": [], "toc_visible": True},
    "kernelspec": {"display_name": "Python 3", "name": "python3"},
    "language_info": {"name": "python"},
}
out = REPO / "workshop/study_buddy_workshop.ipynb"
nbformat.validate(nb)
nbformat.write(nb, out)
print(f"wrote {out} ({out.stat().st_size // 1024} KB, {len(cells)} cells)")
