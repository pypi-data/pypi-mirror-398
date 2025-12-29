import os
import dotenv

from typing import Literal


def create_internet_search_tool(api_key=None):
    from tavily import TavilyClient

    if api_key is None:
        dotenv.load_dotenv()
        api_key = os.getenv("TAVILY_API_KEY")

    tavily_client = TavilyClient(api_key=api_key)

    def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False,
    ):
        """Run a web search. Use this tool if you can't find enough context in recent news."""
        search_docs = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
        return search_docs

    return internet_search
