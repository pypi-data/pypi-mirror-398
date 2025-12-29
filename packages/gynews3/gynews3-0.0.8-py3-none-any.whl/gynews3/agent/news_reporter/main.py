def create_main_agent(
    api_key=None,
    model=None,
    base_url=None,
    subagents=None,
    output_language="Traditional Chinese (繁體中文)",
):
    from deepagents import create_deep_agent

    from gynews3.agent.news_reporter.prompt import main_instruction
    from gynews3.rag import create_model

    if subagents is None:
        from gynews3.agent.news_reporter.sub import create_topic_analysis_sub_agent

        subagents = [create_topic_analysis_sub_agent(output_language=output_language)]

    model = create_model(api_key=api_key, model=model, base_url=base_url)

    return create_deep_agent(
        model=model,
        system_prompt=main_instruction.format(output_language=output_language),
        subagents=subagents,
        debug=True,
    )
