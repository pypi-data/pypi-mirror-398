from pydantic import BaseModel, Field


class Link(BaseModel):
    title: str = Field(description="The title of the resource.")
    purpose: str = Field(description="The purpose or focus of the resource.")
    url: str = Field(description="The URL of the resource.")


class OutputSchema(BaseModel):
    links: list[Link] = Field(
        description="A list of URLs to resources relevant to the specified topic."
    )
    error_message: str = Field(
        description="An error message if any issues occurred during link generation."
    )


def create_main_agent(
    api_key=None,
    model=None,
    base_url=None,
    search_api_key=None,
):
    from deepagents import create_deep_agent

    from gynews3.rag import create_model
    from gynews3.agent import tool
    from gynews3.agent.resource_finder.middleware import PromptMiddleware

    model = create_model(api_key=api_key, model=model, base_url=base_url)

    middleware = [PromptMiddleware()]
    tools = [tool.create_internet_search_tool(api_key=search_api_key)]

    return create_deep_agent(
        model=model,
        middleware=middleware,
        tools=tools,
        response_format=OutputSchema,
        debug=True,
    )
