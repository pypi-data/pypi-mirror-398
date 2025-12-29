from gynews3.agent.news_reporter.prompt import (
    topic_analysis_description,
    topic_analysis_prompt,
)
from gynews3.agent.news_reporter import tool
from gynews3.agent import tool as common_tool
from gynews3 import const


def create_topic_analysis_sub_agent(
    search_api_key=None,
    vector_store=None,
    engine=None,
    days=const.DAYS,
    output_language="Traditional Chinese (繁體中文)",
):
    # internet_search_tool = common_tool.create_internet_search_tool(api_key=search_api_key)
    recent_news_search_tool = tool.create_recent_news_search_tool(
        vector_store=vector_store, days=days
    )
    recent_news_list_tool = tool.create_recent_news_list_tool(engine=engine, days=days)

    return {
        "name": "topic_analysis_agent",
        "description": topic_analysis_description,
        "system_prompt": topic_analysis_prompt.format(output_language=output_language),
        "tools": [
            # internet_search_tool,
            recent_news_search_tool,
            recent_news_list_tool,
        ],
    }
