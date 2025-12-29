main_instruction = """Call write_todos tool first to create a todos. Use the *task function tool* to perform each todo item step by step.

# Topic: {topic}
# Target Language/Region: {language}

Main tasks to include in your plan:
(1) **Authority & Official Sources**: Search for the most authoritative official websites, official documentation, major organizations, or standard-setting bodies related to {topic} to establish a foundational and correct understanding of the field.
(2) **News & Trends**: Curate professional media outlets, newsletters, or information aggregators that report on the latest trends, news, or industry dynamics regarding {topic}.
(3) **Experts & Influencers (Blogs/Tutorials)**: Discover influential personal blogs, technical tutorial sites, expert columns, or high-quality instructional resources (e.g., recipes, coding tutorials, music lessons) within the {topic} sphere.
(4) **Communities & Discussions**: Identify large online forums, Q&A communities (e.g., Stack Overflow, Quora), Discord servers, or Reddit subreddits where {topic} enthusiasts gather, in order to understand hot topics, common issues, and community sentiment.

Some rules to follow:
(1) Aim to provide a comprehensive list of diverse sources to achieve the goal of "mastering information in the {topic} field."
(2) For every blog, news platform, forum, or resource discovered, you **MUST** include the direct URL to that platform.
(3) Perform searches using the language most relevant to {topic}. If {language} specifies a particular language (e.g., "Traditional Chinese" or "Japanese"), prioritize resources in that language. However, if the field's primary knowledge base is in English (e.g., programming), you should include high-quality English resources as well.
(4) Think and respond in {language} (or the user's prompt language if unspecified) to ensure the content is culturally and linguistically appropriate.

If you find the gathered information insufficient or discover new points to explore (e.g., specific sub-topics within {topic}), you are free to call the write_todos tool again to add or modify tasks.

After all TODO items are completed, generate the final answer by referencing the collective outputs of all task function tools.

## Important Guidelines for Final Answer:
1. **NO URL LEFT BEHIND**: When generating the final answer, you must include **EVERY** valid URL found by the *task function tool*. Do not summarize, select only a few examples, or omit links. If the tool finds 20 results, list all 20.
2. **Categorization**: Group the URLs logically (e.g., "Official Documentation," "Community Forums," "Top Blogs") to help the user navigate the resources effectively.
3. **Strict Fidelity**: Do not hallucinate URLs. Only use the specific links returned by the tools.
"""
