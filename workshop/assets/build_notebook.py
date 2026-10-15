"""Build workshop/study_buddy_workshop.ipynb from repo prompts + rendered diagrams."""
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

SRC = ("Source Material (optional, extracted from a document uploaded by the user; empty if none was uploaded):\n"
       "{source_material?}\n")

# (prompt, anchor line, grounding text inserted right after the anchor) -- exactly what the repo adds
GROUNDING = {
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
ORCH_SOURCE = ("\nSource Document:\n{source_note?}\nIf a source document is attached, sub-agents read it from shared state. "
               "Only pass them the topic and the outputs of previous steps, as described below.\n")
ORCH_ANCHOR = "Prompt them to optionally upload a supplemental document (e.g., lecture notes or research paper as a pdf).\n"

# base (ungrounded) prompts = repo prompts with the grounding inserts removed
BASE = dict(P)
for name, edits in GROUNDING.items():
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

def md(text, *imgs):
    cells.append(new_markdown_cell(text.strip("\n")))

def img(i, alt):
    return f"![{alt}]({IMG_BASE}/{i}.png)"

def code(text, form=False):
    c = new_code_cell(text.strip("\n"))
    if form:
        c["metadata"]["cellView"] = "form"
    cells.append(c)


# =============================================================================
md(f"""
# Build a NotebookLM-style Study Guide Generator with Gemini and ADK

**DevFest Hamburg 2026 · Hands-on workshop (105 min)**

In this notebook you'll build **Study Buddy**: give it a topic (and optionally your own PDF) and a team of AI agents researches it, plans an outline, writes a full study guide and turns it into practice questions.

{img("app_progress", "Study Buddy app")}

*The finished app. The agents you build here are its backend. The frontend lives in the [GitHub repo](https://github.com/tahreemrasul/study_buddy).*

### What you'll learn
- How to design a **multi-step GenAI workflow** instead of one giant prompt
- The core building blocks of the **Google Agent Development Kit (ADK)**: agents, tools, sessions, state and events
- How to **ground** generation in a user's own document
- When an **LLM orchestrator** helps, and when plain sequential code is the better choice
- How to **serve** your agents as a backend API that a frontend can call

### You need
- A Google account (for Colab)
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey) (free)
""", "app_progress")

md(f"""
## The big picture

{img("d_architecture", "System architecture")}

The app has three parts. Everything inside the dashed box, the **backend**, is what we build in this notebook. At the end we'll serve it with `adk api_server`, exactly as the real app does, and then walk through how the Next.js frontend talks to it.

{img("d_roadmap", "Build roadmap")}

| Section | Time |
|---|---|
| 0 · Setup | 10 min |
| 1 · The root agent | 10 min |
| 2 · First specialist: topic overview | 10 min |
| 3 · Research: queries + search tools | 12 min |
| 4 · Outline and study guide | 8 min |
| 5 · Q&A | 7 min |
| 6 · The full pipeline | 13 min |
| 7 · Grounding in your own PDF | 15 min |
| Design checkpoint · do we need an orchestrator? | 8 min |
| 8 · Serving the backend + the frontend | 12 min |

Exercises are marked **✏️ Exercise**. Solutions are in collapsed cells: double-click to reveal them.
""", "d_architecture", "d_roadmap")

# =============================================================================
md("""
---
# 0 · Setup

### 0.1 Install the libraries
- **`google-adk`**: the Agent Development Kit
- **`google-genai`**: the Gemini SDK that ADK uses under the hood
- **`pypdf`**: extracts text from PDFs (Section 7)
- **`arxiv`**, **`wikipedia`**: the search tools our research agent will use

Versions are pinned to match the repo.

> If Colab shows a *"Restart session"* button after installing, click it and continue with the next cell.
""")
code("""
!pip install -q google-adk==1.10.0 google-genai==1.29.0 pypdf==6.20.1 arxiv==2.2.0 wikipedia==1.4.0
""")

md("""
### 0.2 Add your Gemini API key
1. Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. In Colab, click the **🔑 key icon** in the left sidebar → **Add new secret**.
3. Name it **`GEMINI_API_KEY`**, paste the key, and switch on **Notebook access**.

Secrets keep your key out of the notebook, so you can share it safely.

`GOOGLE_GENAI_USE_VERTEXAI=FALSE` tells the SDK to use the **Gemini API** (AI Studio key) rather than Vertex AI on Google Cloud.
""")
code("""
import os

try:
    from google.colab import userdata
    os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
except ImportError:
    pass  # running outside Colab: set GEMINI_API_KEY in your environment instead

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
assert os.environ.get("GEMINI_API_KEY"), "Add GEMINI_API_KEY to Colab Secrets (key icon on the left)"
print("API key loaded ✓")
""")

md("""
### 0.3 Pick a model and say hello
We use **`gemini-3.8-flash`** throughout. It's fast and capable enough for every step. A one-line call with the plain Gemini SDK checks that the key works before we bring in ADK.
""")
code("""
import logging
from google import genai

# Hide the SDK's "non-text parts in the response" notices (Gemini's internal thought signatures)
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

MODEL_NAME = "gemini-3.8-flash"

client = genai.Client()
response = client.models.generate_content(model=MODEL_NAME, contents="In one sentence: what is a study guide?")
print(response.text)
""")

md("""
### 0.4 Make the model patient
Free-tier keys have a **per-minute rate limit**. Our full pipeline makes a dozen or more model calls in a couple of minutes, enough to hit it, and the API then answers **`429 RESOURCE_EXHAUSTED`**.

Rather than crash, we tell ADK to **retry with exponential backoff**: wait 5s, then 10s, 20s… (max 60s) and try again, up to 8 times. ADK's `Gemini` model class takes these `retry_options`; every agent below shares this one `MODEL` object.

> You'll see runs pause for a while when the limit is hit. That's the retry waiting, not a hang.
""")
code("""
from google.adk.models.google_llm import Gemini
from google.genai import types

MODEL = Gemini(
    model=MODEL_NAME,
    retry_options=types.HttpRetryOptions(attempts=8, initial_delay=5, max_delay=60, exp_base=2),
)
print("Model ready:", MODEL.model)
""")

# =============================================================================
md(f"""
---
# 1 · The root agent

Every ADK app has a **root agent**: the agent that receives the user's message. Let's start with the simplest possible version: one agent, one instruction, *"write a study guide"*.

First, the ADK concepts we'll use all the way through:

{img("d_adk", "ADK concepts")}

| Concept | What it is |
|---|---|
| **Agent** (`LlmAgent`) | A model + an instruction (+ optional tools). Decides what to say or which tool to call. |
| **Runner** | Executes an agent: builds the prompt, calls the model, runs tools, records everything. |
| **Session** | One conversation. Holds the list of **events** and a shared **state** dict. |
| **Event** | One thing that happened: a model reply, a tool call, a tool result, a state change. |
""", "d_adk")

md("""
### 1.1 A helper to run any agent
We'll run many agents, so here's one helper that:
1. creates a fresh **session** (optionally with initial **state**, which we'll need in Section 7),
2. sends the user's message through a **Runner**,
3. prints each **event** as it arrives, so you can watch the agent work,
4. returns the final text and the session's final state.

You don't need to memorise this. Just notice the three steps: **create session → `runner.run_async(...)` → read events**.
""")
code('''
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME = "study_guide"
USER_ID = "student"
session_service = InMemorySessionService()
LAST_RUN = {}  # stats from the most recent run_agent call


def show_event(event):
    """Print a one-line summary of an ADK event."""
    who = event.author
    for part in (event.content.parts if event.content and event.content.parts else []):
        if part.function_call:
            args = json.dumps(part.function_call.args or {})
            print(f"  [{who}] → calls {part.function_call.name}({args[:120]}{'…' if len(args) > 120 else ''})")
        elif part.function_response:
            print(f"  [{who}] ← {part.function_response.name} returned")
        elif part.text and not part.thought:
            text = " ".join(part.text.split())
            print(f"  [{who}] says: {text[:160]}{'…' if len(text) > 160 else ''}")
    if event.actions and event.actions.state_delta:
        print(f"  [{who}] state += {list(event.actions.state_delta)}")


async def run_agent(agent, message, state=None, verbose=True):
    """Run `agent` on one user message in a fresh session. Returns (final_text, final_state)."""
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, state=state or {})
    content = types.Content(role="user", parts=[types.Part(text=message)])

    final_text = ""
    root_turns = 0  # model responses written by the root agent itself (not by its tools)
    async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=content):
        if verbose:
            show_event(event)
        parts = event.content.parts if event.content and event.content.parts else []
        if event.author == agent.name and any(p.function_call or (p.text and not p.thought) for p in parts):
            root_turns += 1
        if event.is_final_response() and parts:
            final_text = "".join(p.text or "" for p in parts if not p.thought)

    LAST_RUN.update(root_turns=root_turns)
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session.id)
    return final_text, session.state

print("Helper ready ✓")
''')

md("""
### 1.2 The naive root agent
An `LlmAgent` needs a **name**, a **model** and an **instruction** (its system prompt). That's it.
""")
code('''
from google.adk.agents import LlmAgent
from IPython.display import Markdown, display

naive_root = LlmAgent(
    name="study_guide",
    model=MODEL,
    instruction="You create study guides. Write a concise study guide in Markdown on the topic the user gives you.",
)

guide, state = await run_agent(naive_root, "photosynthesis")
display(Markdown(guide[:2500] + ("\\n\\n*… (truncated)*" if len(guide) > 2500 else "")))
''')

md(f"""
### 1.3 So… are we done?
That looks decent! But think about what NotebookLM-style tools need, and what this agent **can't** do:

{img("d_monolith", "One agent vs specialists")}

- **No research.** Everything comes from what the model happens to remember. For niche or new topics, it will guess.
- **No grounding.** It can't use *your* lecture notes.
- **No visibility.** The UI can't show progress: one opaque call, then a wall of text.
- **No reuse.** The outline and the questions aren't separate outputs you can render or regenerate.

So we split the work into **specialists**, each with one job and a small, focused prompt, and turn the root agent into an **orchestrator** that calls them. That's the rest of this notebook.
""", "d_monolith")

# =============================================================================
md("""
---
# 2 · First specialist: the topic overview

The first specialist writes a short overview of the topic. Later agents build on it: the query planner uses it to decide what to search for.

Two new ideas:
- **`description`**: tells *other agents* what this agent does. The orchestrator reads it when deciding which tool to call.
- **`output_key`**: ADK saves the agent's final answer into **session state** under this key, so later steps (and the frontend!) can read it.

Here is the prompt from the real app:
""")
code(py_str("TOPIC_OVERVIEW_PROMPT", BASE["TOPIC_OVERVIEW_PROMPT"]))
code('''
topic_overview_agent = LlmAgent(
    name="topic_overview_agent",
    model=MODEL,
    description="responsible for creating a brief, concise and coherent overview of the topic provided",
    instruction=TOPIC_OVERVIEW_PROMPT,
    output_key="topic_overview",
)

overview, state = await run_agent(topic_overview_agent, "photosynthesis")
print("\\nState keys:", list(state))
''')

md(f"""
Notice the last line of output: **`state += ['topic_overview']`**. Thanks to `output_key`, the overview now lives in session state.

### 2.1 Giving the specialist to the root agent
How does the root agent *use* this specialist? In ADK there are two ways to connect agents:

{img("d_agenttool", "AgentTool vs sub_agents")}

Study Buddy uses **`AgentTool`**: the root agent calls the specialist **like a function**, gets the result back and stays in charge of the workflow. (With `sub_agents`, control would be *transferred* to the child, which is great for routing conversations but not for a pipeline.)
""", "d_agenttool")
code('''
from google.adk.tools.agent_tool import AgentTool

root_v2 = LlmAgent(
    name="study_guide",
    model=MODEL,
    instruction=(
        "You help users create study guides. When the user gives a topic, call topic_overview_agent "
        "with the topic and present the overview under the heading 'Topic Overview for [Topic]'."
    ),
    tools=[AgentTool(agent=topic_overview_agent)],
)

_, state = await run_agent(root_v2, "black holes")
print("\\nState keys:", list(state))
''')

md("""
Read the event log from top to bottom:
1. `[study_guide] → calls topic_overview_agent({"request": "..."})`: the root agent decided to use its tool. The argument is a single **`request`** string: *that's all the specialist sees of the conversation.* Remember this; it matters in Section 7.
2. `← topic_overview_agent returned`: the result came back to the root agent.
3. `state += ['topic_overview']`: the specialist's `output_key` was copied into the **root's** session state.
4. The root agent presents the result.

### ✏️ Exercise 2.1 (2 min)
Make the overview suit a different audience. Copy `TOPIC_OVERVIEW_PROMPT`, add one line such as *"Write for a high-school student, avoiding jargon"*, build a new agent with it and run it on the same topic. Compare the two outputs.
""")
code('''
# ✏️ Your code here
''')
code('''
#@title Solution (double-click to show the code)
kid_prompt = TOPIC_OVERVIEW_PROMPT + "\\n- Write for a high-school student. Avoid jargon and explain any technical term you use.\\n"
kid_overview_agent = LlmAgent(name="topic_overview_agent", model=MODEL, instruction=kid_prompt, output_key="topic_overview")
kid_overview, _ = await run_agent(kid_overview_agent, "photosynthesis", verbose=False)
print(kid_overview)
''', form=True)

# =============================================================================
md("""
---
# 3 · Research: query planner + search agent

To go beyond what the model remembers, the app does **research**:
1. a **query planner** turns the overview into 2 focused search queries,
2. a **search agent** runs them against Wikipedia and arXiv using **tools**.

### 3.1 The query planner
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

# For now *we* play orchestrator: pass the overview from Section 2 in as the message.
queries, _ = await run_agent(search_query_agent, f"Topic Overview:\\n{overview}")
print("\\n" + queries)
''')

md(f"""
### 3.2 Tools: plain Python functions
In ADK, a tool can be an ordinary Python function. ADK reads its **name, type hints and docstring** and describes it to Gemini, so **write good docstrings**: they're what the model reads.

{img("d_tools", "How a function becomes a tool")}

These are the two search tools from the app. They never raise: on failure they return a message telling the model to fall back to other sources. That keeps one flaky API from breaking the whole pipeline.
""", "d_tools")
code('''
import time
import urllib.request

import arxiv
import wikipedia

# Wikipedia asks API clients to identify themselves
opener = urllib.request.build_opener()
opener.addheaders = [("User-Agent", "study-buddy/1.0 (research project)")]
urllib.request.install_opener(opener)

_arxiv_client = arxiv.Client(page_size=3, delay_seconds=2, num_retries=1)


def search_arxiv(query: str) -> list[dict]:
    """Search for relevant publications on arXiv"""
    try:
        search = arxiv.Search(query=query, max_results=2, sort_by=arxiv.SortCriterion.Relevance)
        time.sleep(1)
        docs = [{"title": r.title, "content": r.summary} for r in _arxiv_client.results(search)]
        return docs if docs else [{"content": "No results found on Arxiv. Use internal knowledge."}]
    except Exception as e:
        return [{"content": f"arXiv unavailable ({type(e).__name__}). Use Wikipedia and internal knowledge instead."}]


def search_wikipedia(query: str) -> list[dict]:
    """Search for information on Wikipedia"""
    try:
        docs = []
        for title in wikipedia.search(query, results=3):
            try:
                page = wikipedia.page(title, auto_suggest=False)
                docs.append({"title": page.title, "content": page.summary})
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                continue
        return docs if docs else [{"content": "No results found on Wikipedia. Use internal knowledge."}]
    except Exception:
        return [{"content": "No results found on Wikipedia. Use internal knowledge."}]


# Tools are just functions: test them directly, no model involved
for doc in search_wikipedia("light-dependent reactions"):
    print("•", doc.get("title"), "→", doc["content"][:100], "…")
''')

md("""
### 3.3 The search agent
Now give both tools to an agent. The prompt tells it *how* to use them; Gemini decides *which* tool to call for each query.
""")
code(py_str("SEARCH_PROMPT", BASE["SEARCH_PROMPT"]))
code('''
search_agent = LlmAgent(
    name="search_agent",
    model=MODEL,
    description="Responsible for conducting search for a particular topic given a search query",
    instruction=SEARCH_PROMPT,
    tools=[search_arxiv, search_wikipedia],
    output_key="search",
)

search_results, _ = await run_agent(search_agent, f"Search Query List:\\n{queries}")
''')

md("""
Watch the `→ calls search_wikipedia(...)` / `→ calls search_arxiv(...)` lines: that's Gemini choosing tools and ADK executing your Python functions. This is a place where an LLM **earns its keep**: deciding which source fits each query is a real judgment call.

### ✏️ Exercise 3.1 (3 min)
Send the search agent a query that only a research database would answer well (e.g. *"recent transformer efficiency papers 2024"*) and one that's encyclopedic (e.g. *"history of the printing press"*). Does it pick different tools?
""")
code('''
# ✏️ Your code here
''')
code('''
#@title Solution (double-click to show the code)
for q in ["recent papers on efficient transformer attention", "history of the printing press"]:
    print(f"\\n=== {q}")
    await run_agent(search_agent, f"Search Query List:\\n1. {q}")
''', form=True)

# =============================================================================
md("""
---
# 4 · Outline and study guide

Next, an **outline agent** plans the structure and a **study guide agent** writes the full guide.

Look at what each needs as input:
- outline ← overview + search results
- study guide ← overview + search results + outline

**Context has to be passed from step to step.** Right now we're doing that by hand, pasting earlier outputs into each message. In Section 6 we hand this job to the orchestrator.
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

outline, _ = await run_agent(
    outline_agent,
    f"Topic Overview:\\n{overview}\\n\\nSearch Results:\\n{search_results}",
)
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
display(Markdown(study_guide[:3000] + "\\n\\n*… (truncated, scroll the full text with `print(study_guide)`)*"))
''')

md("""
> **Prompt detail worth stealing:** the study guide prompt says *"Only list resources that actually appear in the Search Results… Never invent titles, authors or publications."* Without that line, models happily produce realistic-looking but fake citations in a "Resources" section. Grounded apps need explicit rules like this.
""")

# =============================================================================
md("""
---
# 5 · Q&A: output a program can use

The last specialist turns the guide into practice questions. Unlike the guide, this output is read by **code**: the frontend renders it as flashcards. So the prompt asks for **JSON** with a difficulty level per question.
""")
code(py_str("QUESTION_ANSWER_PROMPT", BASE["QUESTION_ANSWER_PROMPT"]))
code('''
question_answer_agent = LlmAgent(
    name="question_answer_agent",
    model=MODEL,
    description="responsible for creating question-answer pairs from study guide",
    instruction=QUESTION_ANSWER_PROMPT,
    output_key="question_answer",
)

qa_raw, _ = await run_agent(question_answer_agent, f"Study Guide:\\n{study_guide}", verbose=False)


def parse_qa(raw: str) -> list[dict]:
    """Same logic as the frontend: strip ```json fences, accept a list or {"key": [...]}."""
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    return data if isinstance(data, list) else []


qa = parse_qa(qa_raw)
rows = "\\n".join(f"| {q.get('difficulty', '')} | {q.get('question', '')} |" for q in qa)
display(Markdown(f"**{len(qa)} questions**\\n\\n| Difficulty | Question |\\n|---|---|\\n{rows}"))
''')

md("""
Look at `parse_qa`: stripping code fences and guessing the wrapper key is **fragile**. The model *usually* returns valid JSON, but "usually" isn't great for code that renders a UI.

### ✏️ Exercise 5.1 (5 min): structured output
ADK can enforce a JSON shape with **`output_schema`**: pass a Pydantic model and Gemini's response is constrained to it. Define a `QAPair` (question, answer, difficulty) and a `QASet` (list of pairs), then build a `qa_structured_agent` with `output_schema=QASet` and run it on `study_guide`.

*(Note: an agent with `output_schema` can't use tools, which is fine for this one.)*
""")
code('''
# ✏️ Your code here
''')
code('''
#@title Solution (double-click to show the code)
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
    output_schema=QASet,
    output_key="question_answer",
)
qa_json, _ = await run_agent(qa_structured_agent, f"Study Guide:\\n{study_guide}", verbose=False)
qa_set = QASet.model_validate_json(qa_json)  # guaranteed to parse
print(len(qa_set.questions), "questions; first:", qa_set.questions[0].question)
''', form=True)

# =============================================================================
md(f"""
---
# 6 · The full pipeline: an LLM orchestrator

So far *you* passed outputs from step to step. Now we give that job to the root agent: it gets all six specialists as tools and an instruction describing the workflow.

{img("d_pipeline", "Full pipeline")}

This is the real app's orchestrator prompt. Read the **Workflow** section: one block per specialist, each saying what to pass in and what to do with the result, plus *"immediately proceed to next step… do not wait for user feedback"*.
""", "d_pipeline")
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
print("root_agent has", len(root_agent.tools), "specialists")
''')

md("""
### 6.1 Run it
This makes a dozen or more model calls and takes **about 2–3 minutes**. Watch the event stream: you'll see the orchestrator call each specialist in order and the state keys fill up.
""")
code('''
start = time.time()
final_text, full_state = await run_agent(root_agent, "photosynthesis")
orchestrated_seconds = time.time() - start
orchestrator_turns = LAST_RUN["root_turns"]

print(f"\\nDone in {orchestrated_seconds:.0f}s")
print(f"The orchestrator itself made {orchestrator_turns} model calls (on top of the specialists' own calls)")
print("State keys:", list(full_state))
''')
code('''
display(Markdown(full_state.get("study_guide", "*(no study guide; check the event log above)*")))
''')

md("""
### 6.2 What just happened, and what the frontend sees
Every `→ calls …_agent` line is an event the frontend receives. The app's React hook does two simple things with the stream:
- a `functionCall` named `outline_agent` → move the progress bar to step ④,
- a `stateDelta` containing `outline` → fill in the Outline card.

That's why `output_key` matters: **state keys are the contract between the backend and the UI.**

### ✏️ Exercise 6.1 (5 min): add an output
The abstract promised *key concepts* too. Write a `key_concepts_agent` that reads a study guide and returns a glossary of 8–12 terms with one-line definitions (`output_key="key_concepts"`). Test it on `full_state["study_guide"]`.

*To put it in the pipeline you'd add `AgentTool(agent=key_concepts_agent)` to `root_agent.tools` and one more step to the Workflow in `ORCHESTRATOR_PROMPT`. Try it at home: it's another full run.*
""")
code('''
# ✏️ Your code here
''')
code('''
#@title Solution (double-click to show the code)
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
concepts, _ = await run_agent(key_concepts_agent, f"Study Guide:\\n{full_state['study_guide']}", verbose=False)
display(Markdown(concepts))
''', form=True)

# =============================================================================
md(f"""
---
# 7 · Grounding in your own PDF

NotebookLM's core idea: **work from the user's sources**. Let's let users attach a PDF and make it the primary source for the guide.

### 7.1 The design problem
Remember Section 2? A specialist called through `AgentTool` sees only the **`request` string** the orchestrator writes. If we attached the PDF to the user's message, only the orchestrator would see it, not the specialists who actually write the guide.

What *does* reach every specialist? **Session state.** `AgentTool` copies the parent's state into each specialist's session, and an instruction can read state with a `{{placeholder}}`.

{img("d_grounding", "Getting the PDF to every agent")}

### 7.2 Three ways we could do it
| Option | How | Verdict |
|---|---|---|
| Attach the PDF to the chat message | Gemini reads the PDF natively | Only the orchestrator sees it, and it's re-sent on every orchestrator call |
| Have Gemini summarise the PDF into notes first | One extra model call | Agents are then grounded in an **AI-written summary**, which may drop or invent details |
| **Extract the text with a parser, put it in state when the session is created** | `pypdf`, no model | **Deterministic, cheap, every specialist sees the real text** ✓ |

We use the third. Ingestion is a **preprocessing step**, not something that needs an agent.
""", "d_grounding")

md("""
### 7.3 Get a PDF
We'll use a short lecture about **Lake Varnholm**, a lake that *doesn't exist*. Every fact in it is made up (the "Brekke layer", the "Varnholm Turnover Index", the fish *Salvelinus varnholmi*…). That makes it a perfect test: **if those details show up in the guide, they can only have come from the PDF.**
""")
code('''
PDF_PATH = "varnholm_lecture.pdf"
SAMPLE_PDF_URL = "https://raw.githubusercontent.com/tahreemrasul/study_buddy/main/workshop/data/varnholm_lecture.pdf"

if not os.path.exists(PDF_PATH):
    urllib.request.urlretrieve(SAMPLE_PDF_URL, PDF_PATH)
print("PDF ready:", PDF_PATH, f"({os.path.getsize(PDF_PATH) // 1024} KB)")
''')

md("""
### 7.4 PDF → session state
This function is **exactly** what the app's backend proxy (`api/server.py`) runs when a user uploads a PDF. It returns a dict ready to become the session's initial state:
- `source_material`: the extracted text, read by the specialists
- `source_name`: shown in the guide's Resources section
- `source_note`: one sentence for the orchestrator: *a document is attached, don't paste it into requests*
- `source_error`: set instead if the PDF can't be read (e.g. a scanned PDF with no text layer)
""")
code('''
from pypdf import PdfReader

MAX_SOURCE_CHARS = 100_000  # the text is injected into several prompts, so cap it


def pdf_to_state(path: str) -> dict:
    """Extract a PDF's text with pypdf and return it as initial session state."""
    name = os.path.basename(path)
    try:
        text = "\\n\\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip()
    except Exception as e:
        return {"source_error": f"Could not read {name} ({type(e).__name__})"}
    if not text:
        return {"source_error": f"No extractable text in {name} (scanned PDF?)"}
    return {
        "source_name": name,
        "source_material": text[:MAX_SOURCE_CHARS],
        "source_truncated": len(text) > MAX_SOURCE_CHARS,
        "source_note": (
            f"The user attached a document named '{name}'. Its text is already available "
            "to every sub-agent, so do not paste it into tool requests. "
            "If the user gave no explicit topic, use the document's main subject as the topic."
        ),
    }


source_state = pdf_to_state(PDF_PATH)
print({k: (v[:80] + "…" if isinstance(v, str) and len(v) > 80 else v) for k, v in source_state.items()})
''')

md("""
### 7.5 Teach the specialists to read it
Each specialist that writes content gets a **Source Material** input plus one rule saying how to use it. The placeholder is **`{source_material?}`**: the **`?`** makes it optional, so when no PDF was uploaded ADK fills in an empty string instead of raising an error. One set of prompts handles both cases.

| Agent | Grounding rule |
|---|---|
| topic overview | base the overview on the document |
| query planner | search for background the document *doesn't* explain (don't re-search what it covers) |
| outline | follow the document's structure |
| study guide | the document is the primary source; search only fills gaps; list it first in Resources |
| search, Q&A | unchanged: search just runs queries; Q&A already uses only the (now grounded) guide |
""")
code('SOURCE_INPUT = ' + repr(SRC) + '\n\n'
     'GROUNDING = {\n' +
     "".join(f"    {name!r}: [\n" + "".join(f"        ({a!r},\n         {t!r}),\n" for a, t in edits[1:]) + "    ],\n"
             for name, edits in GROUNDING.items()) +
     '}\n\n'
     'INPUT_ANCHORS = {\n' +
     "".join(f"    {name!r}: {edits[0][0]!r},\n" for name, edits in GROUNDING.items()) +
     '}\n' + '''

def ground(name: str, prompt: str) -> str:
    """Insert the Source Material input and the grounding rules into a prompt."""
    anchor = INPUT_ANCHORS[name]
    prompt = prompt.replace(anchor, anchor + SOURCE_INPUT)
    for anchor, rule in GROUNDING[name]:
        prompt = prompt.replace(anchor, anchor + rule)
    return prompt


GROUNDED = {
    "TOPIC_OVERVIEW_PROMPT": ground("TOPIC_OVERVIEW_PROMPT", TOPIC_OVERVIEW_PROMPT),
    "SEARCH_QUERY_PROMPT": ground("SEARCH_QUERY_PROMPT", SEARCH_QUERY_PROMPT),
    "OUTLINE_PROMPT": ground("OUTLINE_PROMPT", OUTLINE_PROMPT),
    "STUDY_GUIDE_PROMPT": ground("STUDY_GUIDE_PROMPT", STUDY_GUIDE_PROMPT),
}
print(GROUNDED["TOPIC_OVERVIEW_PROMPT"])
''')

md("""
Now rebuild those four specialists with the grounded prompts, and give the orchestrator its `{source_note?}` line.
""")
code('''
topic_overview_agent = LlmAgent(
    name="topic_overview_agent", model=MODEL, output_key="topic_overview",
    description="responsible for creating a brief, concise and coherent overview of the topic provided",
    instruction=GROUNDED["TOPIC_OVERVIEW_PROMPT"],
)
search_query_agent = LlmAgent(
    name="search_query_agent", model=MODEL, output_key="search_queries",
    description="responsible for generating search queries for conducting search on a particular topic",
    instruction=GROUNDED["SEARCH_QUERY_PROMPT"],
)
outline_agent = LlmAgent(
    name="outline_agent", model=MODEL, output_key="outline",
    description=("responsible for creating a structured, high-level outline for a study guide "
                 "based on a given topic and/or supplemental material."),
    instruction=GROUNDED["OUTLINE_PROMPT"],
)
study_guide_agent = LlmAgent(
    name="study_guide_agent", model=MODEL, output_key="study_guide",
    description=("Responsible for creating a detailed, study guide on topic provided by user "
                 "based on search material and outline"),
    instruction=GROUNDED["STUDY_GUIDE_PROMPT"],
)

ORCH_ANCHOR = ''' + repr(ORCH_ANCHOR) + '''
ORCHESTRATOR_PROMPT_GROUNDED = ORCHESTRATOR_PROMPT.replace(ORCH_ANCHOR, ORCH_ANCHOR + ''' + repr(ORCH_SOURCE) + ''')

grounded_root_agent = LlmAgent(
    name="study_guide",
    model=MODEL,
    description=root_agent.description,
    instruction=ORCHESTRATOR_PROMPT_GROUNDED,
    tools=[
        AgentTool(agent=topic_overview_agent),
        AgentTool(agent=search_query_agent),
        AgentTool(agent=search_agent),
        AgentTool(agent=outline_agent),
        AgentTool(agent=study_guide_agent),
        AgentTool(agent=question_answer_agent),
    ],
)
print("Grounded agents ready ✓")
''')

md("""
### 7.6 See grounding work
Run the **same** overview agent twice on the same message: once with an empty session, once with the PDF in state. Only the state differs.
""")
code('''
msg = "Create a study guide from the attached document."

print("=== WITHOUT the PDF in state")
no_pdf, _ = await run_agent(topic_overview_agent, msg, verbose=False)
print(no_pdf[:600])

print("\\n=== WITH the PDF in state")
with_pdf, _ = await run_agent(topic_overview_agent, msg, state=source_state, verbose=False)
print(with_pdf[:600])
''')

md("""
Without the PDF the agent has nothing to work with. With it, the overview is full of Lake Varnholm details no model could know.

### 7.7 The full grounded pipeline
Same root agent design as Section 6, but the session **starts** with the PDF in state. *(~3 minutes: a good moment for questions.)*
""")
code('''
_, grounded_state = await run_agent(grounded_root_agent, msg, state=source_state)

guide_text = grounded_state.get("study_guide", "")
for fact in ["Brekke", "VTI", "0.35", "2.4 mg/L", "Salvelinus varnholmi"]:
    print(f"{'✓' if fact in guide_text else '✗'} {fact}")
''')
code('''
display(Markdown(guide_text))
''')

md("""
Scroll to **Resources** at the end: the PDF is listed first, and there are no invented citations.

### ✏️ Exercise 7.1 (3 min): your own document
Upload a PDF of your own (lecture notes, a paper, documentation…) and run the **overview agent** on it. *(The full pipeline works too, but takes ~3 minutes.)*
""")
code('''
# ✏️ Your code here
''')
code('''
#@title Solution (double-click to show the code)
from google.colab import files

uploaded = files.upload()  # pick a PDF
my_pdf = next(iter(uploaded))
my_state = pdf_to_state(my_pdf)
if "source_error" in my_state:
    print(my_state["source_error"])
else:
    my_overview, _ = await run_agent(topic_overview_agent, msg, state=my_state, verbose=False)
    print(my_overview)
''', form=True)

# =============================================================================
md(f"""
---
# Design checkpoint: do we need an LLM orchestrator?

Look back at the Section 6 event log. Our six steps **always run in the same order**, yet every time, the orchestrator spends a model call deciding *"what next?"*, and it could in principle skip a step or stop to ask the user something.

{img("d_sequential", "Orchestrator vs SequentialAgent")}

ADK has **workflow agents** that run sub-agents in a fixed order *without* a model in the loop: `SequentialAgent`, `ParallelAgent` and `LoopAgent`. With a `SequentialAgent`, the steps can't pass context through an orchestrator's request text, so each one reads its inputs **from state** instead: `{{topic_overview}}`, `{{outline}}`… All of those are already there thanks to `output_key`.
""", "d_sequential")
code('''
from google.adk.agents import SequentialAgent

# What each step reads from state (written by the earlier steps' output_key)
INPUTS = {
    "search_query_agent": "Topic Overview:\\n{topic_overview}",
    "search_agent": "Search Query List:\\n{search_queries}",
    "outline_agent": "Topic Overview:\\n{topic_overview}\\n\\nSearch Results:\\n{search}",
    "study_guide_agent": "Topic Overview:\\n{topic_overview}\\n\\nSearch Results:\\n{search}\\n\\nOutline:\\n{outline}",
    "question_answer_agent": "Study Guide:\\n{study_guide}",
}


def as_step(agent: LlmAgent) -> LlmAgent:
    """Copy a specialist, appending the state inputs it needs to its instruction."""
    inputs = INPUTS.get(agent.name, "")
    return agent.model_copy(update={"instruction": agent.instruction + ("\\n\\nInputs:\\n" + inputs if inputs else "")})


sequential_pipeline = SequentialAgent(
    name="study_guide",
    sub_agents=[as_step(a) for a in [topic_overview_agent, search_query_agent, search_agent,
                                    outline_agent, study_guide_agent, question_answer_agent]],
)

start = time.time()
_, seq_state = await run_agent(sequential_pipeline, "photosynthesis")
sequential_seconds = time.time() - start

print(f"\\nModel calls spent on orchestration:  LLM orchestrator {orchestrator_turns}  ·  SequentialAgent {LAST_RUN['root_turns']}")
print(f"Wall-clock time:                     LLM orchestrator {orchestrated_seconds:.0f}s  ·  SequentialAgent {sequential_seconds:.0f}s")
print("Same outputs in state:", all(k in seq_state for k in ["topic_overview", "search_queries", "search",
                                                          "outline", "study_guide", "question_answer"]))
''')

md("""
**Reading the numbers.** The orchestrator spends its own model calls deciding what to call next and *presenting* each result. Look at the Section 6 log: it re-types the whole study guide and the Q&A JSON in its replies, which costs output tokens on top of the specialists' work. The SequentialAgent spends **zero** calls on orchestration. Wall-clock time is noisy on a free-tier key because rate-limit retries dominate it, so compare the call counts.

**So which should you use?**
- **`SequentialAgent`** when the steps are fixed: fewer model calls and tokens, predictable, and guaranteed to run every step. For this pipeline it's arguably the better choice.
- **LLM orchestrator** when the next step genuinely depends on the content or the conversation: *"make the guide shorter"*, *"just redo the questions"*. The app keeps the orchestrator for that flexibility (see the end of its prompt: *"If you receive a follow up request, trigger the necessary agent"*).
- A useful middle ground: a fixed `SequentialAgent` pipeline for generation, with an LLM agent only for follow-up chat.

**Rule of thumb: put an LLM where a decision depends on the content (which tool to search with), and plain code where it doesn't.**
""")

# =============================================================================
md(f"""
---
# 8 · Serving it as a backend

Everything so far ran *inside* this notebook. A web app needs an **HTTP API**. ADK ships one: point **`adk api_server`** at a folder of agents and it serves them.

### 8.1 Package the agents
ADK expects one folder per app, with an `agent.py` that defines **`root_agent`**:

```
backend/
└── study_guide/
    ├── __init__.py      # from . import agent
    ├── agent.py         # all agents + root_agent
    ├── prompts.py       # the prompts we wrote above
    └── tools.py         # search_wikipedia, search_arxiv
```

*(The repo splits this into one folder per specialist under `api/study_guide/sub_agents/`. Same agents, more files.)*
""")
code('''
import inspect
from pathlib import Path

pkg = Path("backend/study_guide")
pkg.mkdir(parents=True, exist_ok=True)

(pkg / "__init__.py").write_text("from . import agent\\n")

prompts = {
    "ORCHESTRATOR_PROMPT": ORCHESTRATOR_PROMPT_GROUNDED,
    "TOPIC_OVERVIEW_PROMPT": GROUNDED["TOPIC_OVERVIEW_PROMPT"],
    "SEARCH_QUERY_PROMPT": GROUNDED["SEARCH_QUERY_PROMPT"],
    "SEARCH_PROMPT": SEARCH_PROMPT,
    "OUTLINE_PROMPT": GROUNDED["OUTLINE_PROMPT"],
    "STUDY_GUIDE_PROMPT": GROUNDED["STUDY_GUIDE_PROMPT"],
    "QUESTION_ANSWER_PROMPT": QUESTION_ANSWER_PROMPT,
}
(pkg / "prompts.py").write_text("\\n\\n".join(f"{k} = {v!r}" for k, v in prompts.items()) + "\\n")

tools_header = ("import time\\nimport urllib.request\\n\\nimport arxiv\\nimport wikipedia\\n\\n"
                "opener = urllib.request.build_opener()\\n"
                "opener.addheaders = [('User-Agent', 'study-buddy/1.0 (research project)')]\\n"
                "urllib.request.install_opener(opener)\\n\\n"
                "_arxiv_client = arxiv.Client(page_size=3, delay_seconds=2, num_retries=1)\\n\\n\\n")
(pkg / "tools.py").write_text(tools_header + inspect.getsource(search_arxiv) + "\\n\\n" + inspect.getsource(search_wikipedia))

print(*sorted(str(p) for p in pkg.iterdir()), sep="\\n")
''')
code(f'''
%%writefile backend/study_guide/agent.py
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from . import prompts
from .tools import search_arxiv, search_wikipedia

# Same model + retry settings as in the notebook (Section 0.4)
MODEL = Gemini(
    model="{'gemini-3.8-flash'}",
    retry_options=types.HttpRetryOptions(attempts=8, initial_delay=5, max_delay=60, exp_base=2),
)

topic_overview_agent = LlmAgent(
    name="topic_overview_agent", model=MODEL, output_key="topic_overview",
    description="responsible for creating a brief, concise and coherent overview of the topic provided",
    instruction=prompts.TOPIC_OVERVIEW_PROMPT,
)
search_query_agent = LlmAgent(
    name="search_query_agent", model=MODEL, output_key="search_queries",
    description="responsible for generating search queries for conducting search on a particular topic",
    instruction=prompts.SEARCH_QUERY_PROMPT,
)
search_agent = LlmAgent(
    name="search_agent", model=MODEL, output_key="search",
    description="Responsible for conducting search for a particular topic given a search query",
    instruction=prompts.SEARCH_PROMPT,
    tools=[search_arxiv, search_wikipedia],
)
outline_agent = LlmAgent(
    name="outline_agent", model=MODEL, output_key="outline",
    description="responsible for creating a structured, high-level outline for a study guide based on a given topic and/or supplemental material.",
    instruction=prompts.OUTLINE_PROMPT,
)
study_guide_agent = LlmAgent(
    name="study_guide_agent", model=MODEL, output_key="study_guide",
    description="Responsible for creating a detailed, study guide on topic provided by user based on search material and outline",
    instruction=prompts.STUDY_GUIDE_PROMPT,
)
question_answer_agent = LlmAgent(
    name="question_answer_agent", model=MODEL, output_key="question_answer",
    description="responsible for creating question-answer pairs from study guide",
    instruction=prompts.QUESTION_ANSWER_PROMPT,
)

root_agent = LlmAgent(
    name="study_guide",
    model=MODEL,
    description="Creates a structured, detailed study guide on a given topic based on search results and an outline",
    instruction=prompts.ORCHESTRATOR_PROMPT,
    tools=[AgentTool(agent=a) for a in [topic_overview_agent, search_query_agent, search_agent,
                                        outline_agent, study_guide_agent, question_answer_agent]],
)
''')

md(f"""
### 8.2 Start the server
We start `adk api_server` in the background on port 8000. It inherits this notebook's environment, including `GEMINI_API_KEY`. (Locally you'd just run `adk api_server` in a terminal inside `api/`; that's Terminal 1 in the repo's README.)

{img("d_endpoints", "Backend API")}
""", "d_endpoints")
code('''
import shutil
import subprocess
import sys

import requests

ADK = shutil.which("adk") or os.path.join(os.path.dirname(sys.executable), "adk")
server = subprocess.Popen([ADK, "api_server", "--port", "8000", "backend"],
                          stdout=open("adk_server.log", "w"), stderr=subprocess.STDOUT)

BASE_URL = "http://127.0.0.1:8000"
for _ in range(60):
    try:
        print("GET /list-apps →", requests.get(f"{BASE_URL}/list-apps", timeout=2).json())
        break
    except requests.ConnectionError:
        time.sleep(1)
else:
    print(open("adk_server.log").read()[-2000:])
''')

md("""
### 8.3 Create a session, with the PDF in state
`POST /apps/{app}/users/{user}/sessions/{session}`: **the JSON body becomes the session's initial state.** This is the same `create_session(state=...)` we've used all along, now over HTTP, and it's exactly what the app's proxy does after parsing an uploaded PDF.
""")
code('''
session_id = f"s_{int(time.time())}"
r = requests.post(f"{BASE_URL}/apps/study_guide/users/{USER_ID}/sessions/{session_id}", json=source_state)
print("Session created with state keys:", list(r.json()["state"]))
''')

md("""
### 8.4 Run it and stream the events
`POST /run_sse` takes the user's message and streams back **Server-Sent Events**: one `data: {...}` line per ADK event, the same events we've been printing all along.

To save time and quota we **stop reading after the first two specialists finish**. Closing the stream also cancels the run on the server.
""")
code('''
body = {
    "appName": "study_guide",
    "userId": USER_ID,
    "sessionId": session_id,
    "newMessage": {"role": "user", "parts": [{"text": "Create a study guide from the attached document."}]},
    "streaming": False,
}

with requests.post(f"{BASE_URL}/run_sse", json=body, stream=True, timeout=600) as stream:
    for line in stream.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        event = json.loads(line[len("data: "):])
        for part in (event.get("content") or {}).get("parts") or []:
            if "functionCall" in part:
                print(f"[{event['author']}] → calls {part['functionCall']['name']}")
        delta = (event.get("actions") or {}).get("stateDelta") or {}
        if delta:
            print(f"[{event['author']}] stateDelta: {list(delta)}")
        if "search_queries" in delta:
            print("\\nTwo specialists done: stopping here.")
            break
''')

md("""
That's the **whole backend contract**:

| Call | Purpose |
|---|---|
| `GET /list-apps` | which agent apps the server found |
| `POST /apps/{app}/users/{user}/sessions/{id}` | create a session; **body = initial state** (our PDF text) |
| `POST /run_sse` | send a message, receive a stream of events (`functionCall`, `stateDelta`, text…) |

Equivalent `curl` calls, for your terminal:
```bash
curl localhost:8000/list-apps
curl -X POST localhost:8000/apps/study_guide/users/u1/sessions/s1 -H "Content-Type: application/json" -d '{}'
curl -N -X POST localhost:8000/run_sse -H "Content-Type: application/json" \\
  -d '{"appName":"study_guide","userId":"u1","sessionId":"s1","newMessage":{"role":"user","parts":[{"text":"photosynthesis"}]}}'
```
""")
code('''
server.terminate()
print("Server stopped.")
''')

# =============================================================================
md(f"""
---
# The frontend

The Next.js app in the repo is a thin layer over the three calls above. Repo: **[github.com/tahreemrasul/study_buddy](https://github.com/tahreemrasul/study_buddy)**

{img("app_input", "Topic input with an attached PDF")}

| Repo file | What it does | Notebook equivalent |
|---|---|---|
| `api/study_guide/` | The agents | Sections 1–7 |
| `api/server.py` | Proxy: adds **CORS** headers (browsers block calls to another port without them) and runs **`pdf_to_state`** when a session is created with a PDF | `pdf_to_state` + 8.3 |
| `web/app/hooks/useStudySession.ts` | Creates the session, opens `/run_sse`, maps `functionCall` names to progress steps and `stateDelta` keys to cards | 8.3–8.4 |
| `web/app/components/` | Progress, Study Guide and Q&A tabs; flashcards render the Q&A JSON | `display(Markdown(...))`, `parse_qa` |

{img("app_guide", "Study guide tab")}

### Run the full app locally
Follow the README: three terminals (`adk api_server`, `uvicorn server:app --port 8001`, `npm run dev`), then open `http://localhost:3000`.
""", "app_input", "app_guide")

md("""
---
# Recap

| You built | ADK concept |
|---|---|
| A root agent | `LlmAgent`, `Runner`, sessions and events |
| Six specialists, one job each | focused prompts, `description`, `output_key` |
| Research with Wikipedia and arXiv | Python functions as **tools** |
| An orchestrator | `AgentTool`: agents calling agents like functions |
| Grounding in a user's PDF | **session state** at creation + `{placeholder?}` |
| A fixed-order alternative | `SequentialAgent`, and when to use which |
| A backend API | `adk api_server`: sessions + `/run_sse` events |

### Make it more NotebookLM
- **Chat with your sources:** a follow-up agent that answers questions using `{source_material?}` and `{study_guide?}`
- **Citations:** ask the guide agent to tag claims with `[source, section]`
- **Multiple documents:** store several sources in state and let the user pick
- **Audio overview:** turn the guide into a two-host script and voice it with Gemini text-to-speech
- **More outputs:** key concepts (Exercise 6.1), revision notes or a timeline, each just another specialist with its own `output_key`

### Resources
- ADK docs: [google.github.io/adk-docs](https://google.github.io/adk-docs/)
- Gemini API: [ai.google.dev](https://ai.google.dev/)
- Workshop repo: [github.com/tahreemrasul/study_buddy](https://github.com/tahreemrasul/study_buddy)

**Thank you, and happy building!**
""")

# ---------------------------------------------------------------- write
nb = new_notebook(cells=cells)
nb.metadata = {
    "colab": {"provenance": [], "toc_visible": True},
    "kernelspec": {"display_name": "Python 3", "name": "python3"},
    "language_info": {"name": "python"},
}
out = REPO / "workshop/study_buddy_workshop.ipynb"
out.parent.mkdir(exist_ok=True)
nbformat.validate(nb)
nbformat.write(nb, out)
print(f"wrote {out} ({out.stat().st_size // 1024} KB, {len(cells)} cells)")
