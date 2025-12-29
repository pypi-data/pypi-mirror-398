def news_reporter_main():
    from gynews3 import rag
    from gynews3.agent.news_reporter.main import create_main_agent
    from gynews3.agent.news_reporter.sub import create_topic_analysis_sub_agent

    document_loader = rag.create_recent_links_document_loader()
    vector_store = rag.create_in_memory_vector_store()

    rag.index(document_loader=document_loader, vector_store=vector_store)

    subagents = [create_topic_analysis_sub_agent(vector_store=vector_store)]

    return create_main_agent(subagents=subagents)


def news_finder_main():
    from gynews3.agent.news_finder.main import create_main_agent

    return create_main_agent()


def resource_finder_main():
    from gynews3.agent.resource_finder.main import create_main_agent

    return create_main_agent()


def create_empty_agent():
    from langchain.agents import create_agent

    return create_agent(lambda _: "No operation")


news_reporter = create_empty_agent()
news_finder = news_finder_main()
resource_finder = resource_finder_main()
