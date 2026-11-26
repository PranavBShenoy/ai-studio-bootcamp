import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from openai import APIStatusError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

load_dotenv()

MODEL = "anthropic/claude-haiku-4.5"
# Claude Haiku 4.5 pricing per 1M tokens ($1.00 input / $5.00 output)
INPUT_COST_PER_M = 1.00
OUTPUT_COST_PER_M = 5.00
USD_TO_INR = 92.55
LOG_FILE = Path("cost_log.csv")


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


def log_usage(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float]:
    cost_usd = (input_tokens / 1_000_000) * INPUT_COST_PER_M + (
        output_tokens / 1_000_000
    ) * OUTPUT_COST_PER_M
    cost_inr = cost_usd * USD_TO_INR

    write_header = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(
                ["timestamp", "model", "input_tokens", "output_tokens", "cost_usd", "cost_inr"]
            )
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                model,
                input_tokens,
                output_tokens,
                f"{cost_usd:.6f}",
                f"{cost_inr:.4f}",
            ]
        )
    return cost_usd, cost_inr


@retry(
    retry=retry_if_exception(is_retryable),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    reraise=True,
)
def stream_turn(client: OpenAI, messages: list[dict]) -> tuple[str, int, int]:
    chunks: list[str] = []
    in_tok = 0
    out_tok = 0

    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=512,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            chunks.append(text)
        if getattr(chunk, "usage", None):
            in_tok = chunk.usage.prompt_tokens or 0
            out_tok = chunk.usage.completion_tokens or 0

    print()
    return "".join(chunks), in_tok, out_tok


def main() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or "your_actual_key_here" in api_key:
        raise RuntimeError("Set a valid OPENROUTER_API_KEY in .env first.")

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    messages: list[dict] = [
        {"role": "system", "content": "You are a concise, helpful engineering assistant."}
    ]
    print(f"Streaming CLI Chat ({MODEL}) — type '/exit' or Ctrl+C to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})
        print("AI: ", end="", flush=True)
        reply, in_tok, out_tok = stream_turn(client, messages)
        messages.append({"role": "assistant", "content": reply})

        cost_usd, cost_inr = log_usage(MODEL, in_tok, out_tok)
        print(f"[tokens: in={in_tok}, out={out_tok} | est: ${cost_usd:.6f} / ₹{cost_inr:.4f}]\n")


if __name__ == "__main__":
    main()
