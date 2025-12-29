import os

import dotenv
from huggingface_hub import InferenceClient


def create_hf_client(api_key: str | None = None) -> InferenceClient:
    if api_key is None:
        dotenv.load_dotenv()
        api_key = os.environ.get("HF_TOKEN")

    return InferenceClient(
        api_key=api_key,
    )


def hf_summarize(client: InferenceClient, text: str) -> str:
    result = client.summarization(
        text,
        model="csebuetnlp/mT5_multilingual_XLSum",
    )
    return result.summary_text


def hf_summarize_deep_seek(client: InferenceClient, text: str) -> str:
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2:novita",
        messages=[
            {
                "role": "user",
                "content": f"摘要以下文章，字數150字內，摘要語言用文章所用語言來寫:\n\n{text}",
            }
        ],
    )

    return completion.choices[0].message.content


def create_model(api_key=None, model=None, base_url=None):
    from langchain.chat_models import init_chat_model

    if any(it is None for it in (api_key, model, base_url)):
        dotenv.load_dotenv()

    if api_key is None:
        api_key = os.getenv("AI_SUMMARIZATION_API_KEY")

    if base_url is None:
        base_url = os.getenv("AI_SUMMARIZATION_BASE_URL")

    if model is None:
        model = os.getenv("AI_SUMMARIZATION_MODEL", "gpt-4o")

    return init_chat_model(
        model,
        base_url=base_url,
        api_key=api_key,
    )


def model_summarize(model, text: str) -> str:
    response = model.invoke(
        f"摘要以下文章，字數150字內，摘要語言用文章所用語言來寫:\n\n{text}"
    )
    return response.text


def gycolab_summarize(text: str, base_url: str | None = None) -> str:
    import httpx

    if base_url is None:
        import dotenv

        dotenv.load_dotenv()

        base_url = os.getenv("GYCOLAB_BASE_URL")

    r = httpx.post(f"{base_url}/summarize", data={"text": text})
    r.raise_for_status()

    return r.json().get("summary_text", "")


def simple_summarize(text: str, head=100, tail=50) -> str:
    if not text:
        return ""

    total_len = len(text)

    if total_len <= (head + tail):
        return f"--- [ len: {total_len} ] ---\n{text}\n---"

    header = text[:head].strip()
    footer = text[-tail:].strip()

    preview = (
        f"--- [ len: {total_len} ] ---\n" f"{header}\n" f"...\n" f"{footer}\n" f"---"
    )

    return preview
