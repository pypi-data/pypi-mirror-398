import os
import dotenv

from gynews3 import const


def create_model(api_key=None, model=None, base_url=None):
    from langchain.chat_models import init_chat_model

    if any(it is None for it in (api_key, model, base_url)):
        dotenv.load_dotenv()

    if api_key is None:
        api_key = os.getenv("AI_API_KEY")

    if base_url is None:
        base_url = os.getenv("AI_BASE_URL")

    if model is None:
        model = os.getenv("AI_MODEL", "gpt-4o")

    return init_chat_model(
        model,
        base_url=base_url,
        api_key=api_key,
    )


def create_embedding(api_key=None, model=None, base_url=None):
    from langchain.embeddings import init_embeddings

    if any(it is None for it in (api_key, model, base_url)):
        dotenv.load_dotenv()

    if api_key is None:
        api_key = os.getenv("AI_EMBEDDINGS_API_KEY")

    if base_url is None:
        base_url = os.getenv("AI_EMBEDDINGS_BASE_URL")

    if model is None:
        model = os.getenv("AI_EMBEDDINGS", "text-embedding-3-large")

    return init_embeddings(
        model=model,
        base_url=base_url,
        api_key=api_key,
        chunk_size=200,
        max_retries=5,
        retry_min_seconds=10,
        show_progress_bar=True,
    )


def create_in_memory_vector_store(embedding=None):
    from langchain_core.vectorstores import InMemoryVectorStore

    if embedding is None:
        embedding = create_embedding()

    return InMemoryVectorStore(embedding=embedding)


def create_recent_links_document_loader(engine=None, days=const.DAYS):
    from langchain_core.document_loaders import BaseLoader
    from langchain_core.documents import Document
    from gynews3 import model

    if engine is None:
        engine = model.create_engine()

    class RecentLinksLoader(BaseLoader):
        def lazy_load(self):
            with model.create_session(engine) as session:
                for link in model.get_recent_links(session, days=days):
                    content = f"title: {link.title or "<blank>"}\n\n{link.content}"
                    metadata = {
                        "url": link.url,
                        "title": link.title,
                        "summary": link.summary,
                        "created_at": link.created_at.isoformat(),
                    }
                    yield Document(page_content=content, metadata=metadata)

    return RecentLinksLoader()


def index(document_loader, vector_store, text_splitter=None):
    if text_splitter is None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )

    docs = document_loader.load()
    splits = text_splitter.split_documents(docs)

    vector_store.add_documents(documents=splits)
