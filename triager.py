import argparse
import csv
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import APIStatusError, OpenAI, RateLimitError
from pydantic import ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from schema import TicketTriage

load_dotenv()

MODEL = "anthropic/claude-haiku-4.5"


def is_retryable_api(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


def get_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing in .env")
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")


def load_prompt(version: str) -> str:
    path = Path("prompts") / f"{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


@retry(
    retry=retry_if_exception(is_retryable_api),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_llm(client: OpenAI, system_prompt: str, messages: list[dict]) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.0,
        max_tokens=300,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return (resp.choices[0].message.content or "").strip()


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def triage_complaint(client: OpenAI, system_prompt: str, complaint: str) -> tuple[TicketTriage, int]:
    messages: list[dict] = [
        {"role": "user", "content": f"<complaint>{complaint}</complaint>"}
    ]
    raw = _call_llm(client, system_prompt, messages)
    attempts = 1

    try:
        parsed = json.loads(_strip_fences(raw))
        return TicketTriage.model_validate(parsed), attempts
    except (json.JSONDecodeError, ValidationError) as err:
        # Retry once with explicit validation feedback
        attempts = 2
        messages.append({"role": "assistant", "content": raw})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Your previous output failed validation: {err}\n"
                    "Return ONLY a single valid JSON object matching: "
                    "{equipment, urgency, hospital, next_action}."
                ),
            }
        )
        raw_retry = _call_llm(client, system_prompt, messages)
        parsed_retry = json.loads(_strip_fences(raw_retry))
        return TicketTriage.model_validate(parsed_retry), attempts


def run_eval(client: OpenAI, version: str, samples_path: Path, out_csv: Path) -> None:
    system_prompt = load_prompt(version)
    rows = []
    correct_count = 0

    with samples_path.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f if line.strip()]

    for idx, item in enumerate(samples):
        if idx > 0:
            time.sleep(3.5)
        pred, attempts = triage_complaint(client, system_prompt, item["complaint"])
        pred_dict = pred.model_dump()
        exp_dict = item["expected"]

        eq_ok = pred_dict["equipment"].strip().lower() == exp_dict["equipment"].strip().lower()
        urg_ok = pred_dict["urgency"] == exp_dict["urgency"]
        hosp_ok = (pred_dict["hospital"] or "").strip().lower() == (
            exp_dict["hospital"] or ""
        ).strip().lower()
        act_ok = pred_dict["next_action"] == exp_dict["next_action"]
        all_ok = eq_ok and urg_ok and hosp_ok and act_ok

        if all_ok:
            correct_count += 1

        rows.append(
            {
                "id": item["id"],
                "prompt_version": version,
                "attempts": attempts,
                "equipment_pred": pred_dict["equipment"],
                "equipment_exp": exp_dict["equipment"],
                "urgency_pred": pred_dict["urgency"],
                "urgency_exp": exp_dict["urgency"],
                "hospital_pred": pred_dict["hospital"] if pred_dict["hospital"] is not None else "null",
                "hospital_exp": exp_dict["hospital"] if exp_dict["hospital"] is not None else "null",
                "next_action_pred": pred_dict["next_action"],
                "next_action_exp": exp_dict["next_action"],
                "passed": all_ok,
            }
        )

    total = len(samples)
    pct = (correct_count / total * 100) if total else 0.0

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "id",
            "prompt_version",
            "attempts",
            "equipment_pred",
            "equipment_exp",
            "urgency_pred",
            "urgency_exp",
            "hospital_pred",
            "hospital_exp",
            "next_action_pred",
            "next_action_exp",
            "passed",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(
            {
                "id": "SUMMARY",
                "prompt_version": version,
                "attempts": "",
                "equipment_pred": f"{correct_count}/{total}",
                "equipment_exp": f"{pct:.1f}%",
                "urgency_pred": "",
                "urgency_exp": "",
                "hospital_pred": "",
                "hospital_exp": "",
                "next_action_pred": "",
                "next_action_exp": "",
                "passed": f"{pct:.1f}%",
            }
        )

    print(f"[{version}] Score: {correct_count}/{total} ({pct:.1f}%) -> saved to {out_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Equipment Complaint Triager CLI")
    parser.add_argument("complaint", nargs="?", help="Free-text equipment complaint")
    parser.add_argument("--prompt", default="v2", choices=["v1", "v2"], help="Prompt version")
    parser.add_argument("--eval", action="store_true", help="Run 20-sample evaluation")
    parser.add_argument("--samples", default="samples.jsonl", help="Path to JSONL samples")
    parser.add_argument("--out", default="accuracy.csv", help="Output CSV path")
    args = parser.parse_args()

    client = get_client()

    if args.eval:
        run_eval(client, args.prompt, Path(args.samples), Path(args.out))
        return

    if not args.complaint:
        parser.error("Provide a complaint string or pass --eval.")

    system_prompt = load_prompt(args.prompt)
    result, attempts = triage_complaint(client, system_prompt, args.complaint)
    print(json.dumps(result.model_dump(), indent=2))
    print(f"(prompt={args.prompt}, attempts={attempts})")


if __name__ == "__main__":
    main()
