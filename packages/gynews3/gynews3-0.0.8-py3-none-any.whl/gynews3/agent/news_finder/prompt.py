main_instruction = """Call write_todos tool first to create a todos. Use the *task function tool* to perform each todo item step by step.

Main tasks to include in your plan:
(1) 搜尋{location}全國性的主要新聞媒體與報社，並找出它們的官方網站，以建立對全國性議題的基礎理解。
(2) 整理{location}各地方（例如：都道府縣）具代表性的地方報紙或電視台新聞網站，並找出它們的官方網站，以了解地域性議題與在地觀點。
(3) 找出{location}主流的部落格平台服務（Blog Service Provider），並找出它們的平台網站。
(4) 發掘{location}大型的網路論壇或問答社群，並找出它們的平台網站，以了解{location}網民關心的熱門話題與輿論動向。

Some rules to follow:
(1) 針對如何「掌握在地資訊與文化」這個目標，提供一份包含各類來源的推薦清單，需附上連結到該平台的網址連結（URL）。
(2) 發掘到的部落格、新聞平台等，需附上連結到該平台的網址連結（URL）。
(3) 使用{location}當地的語言進行搜尋，確保搜尋到的內容符合在地文化。
(4) 思考與回應盡量使用{location}當地的語言，以確保內容的在地相關性與文化適切性。

If you find the gathered information insufficient or discover new points to explore, you are free to call the write_todos tool again to add or modify tasks.

After all TODO items are completed, generate the final answer by referencing the collective outputs of all task function tools.

## Important Guidelines for Final Answer:
1. **NO URL LEFT BEHIND**: When generating the final answer, you must include **EVERY** valid URL found by the *task function tool*. Do not summarize, select only a few examples, or omit links. If the tool finds 20 results, list all 20.
2. **Strict Fidelity**: Do not hallucinate URLs. Only use the specific links returned by the tools.
"""
