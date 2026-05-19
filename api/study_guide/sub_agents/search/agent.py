import urllib.request
import time
import arxiv
import wikipedia
from google.adk.agents import Agent
from study_guide.config.config import MODEL
from . import prompt


opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'study-buddy/1.0 (research project)')]
urllib.request.install_opener(opener)


_arxiv_client = arxiv.Client(
    page_size=3,
    delay_seconds=2,
    num_retries=1
)


def search_arxiv(query: str) -> list[dict]:
    """Search for relevant publications on arXiv"""
    try:
        search = arxiv.Search(
            query=query,
            max_results=2,
            sort_by=arxiv.SortCriterion.Relevance
        )

        time.sleep(1)

        docs = []
        for r in _arxiv_client.results(search):
            docs.append({
                "title": r.title,
                "content": r.summary
            })

        return docs if docs else [{"content": "No results found on Arxiv. Use internal knowledge."}]

    except Exception as e:
        return [{"content": f"arXiv unavailable ({type(e).__name__}). Use Wikipedia and internal knowledge instead."}]


def search_wikipedia(query: str) -> list[dict]:
    """Search for information on Wikipedia"""
    try:
        results = wikipedia.search(query, results=3)
        docs = []
        for title in results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                docs.append({
                    "title": page.title,
                    "content": page.summary
                })
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                continue
        return docs if docs else [{"content": "No results found on Wikipedia. Use internal knowledge."}]
    except Exception:
        return [{"content": "No results found on Wikipedia. Use internal knowledge."}]


search_agent = Agent(
    model=MODEL,
    name="search_agent",
    description="Responsible for conducting search for a particular "
                "topic given a search query",
    output_key="search",
    instruction=prompt.SEARCH_PROMPT,
    tools=[search_arxiv, search_wikipedia]
)