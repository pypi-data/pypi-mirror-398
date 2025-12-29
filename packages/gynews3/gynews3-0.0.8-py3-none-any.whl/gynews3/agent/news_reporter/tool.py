from gynews3 import const


def create_recent_news_search_tool(vector_store=None, days=const.DAYS):
    if vector_store is None:
        from gynews3.rag import create_in_memory_vector_store

        vector_store = create_in_memory_vector_store()

    def recent_news_search(query: str, k: int = 5):
        """Search recent news for relevant content. This will return full news content. Use this tool if you already know what news content to looking for."""
        result = [dict(doc) for doc in vector_store.similarity_search(query, k=k)]

        return result

    return recent_news_search


def create_recent_news_list_tool(engine=None, days=const.DAYS):
    from gynews3 import model

    if engine is None:
        engine = model.create_engine()

    def recent_news_list(offset=0, limit=20):
        """List recent news. This will list news summary only. Use this tool to figure out what keywords to search for detailed news content."""
        with model.create_session(engine) as session:
            links = model.get_recent_links(
                session, offset=offset, limit=limit, days=days
            )
            result = []
            for link in links:
                result.append(
                    {
                        "title": link.title,
                        "url": link.url,
                        "summary": link.summary,
                    }
                )
        return result

    return recent_news_list
