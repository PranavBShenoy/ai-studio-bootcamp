import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

resp = client.chat.completions.create(
    model="anthropic/claude-haiku-4.5",
    max_tokens=128,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print("Reply:", resp.choices[0].message.content)
print("Usage:", resp.usage)
