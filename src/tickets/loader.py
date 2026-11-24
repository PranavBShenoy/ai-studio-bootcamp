import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import ValidationError
from tickets.models import Ticket

logger = logging.getLogger(__name__)


@dataclass
class ValidationSummary:
    valid_tickets: list[Ticket] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)


def load_tickets_csv(csv_path: Path) -> ValidationSummary:
    summary = ValidationSummary()
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        logger.warning("CSV file missing or empty: %s", csv_path)
        return summary

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            cleaned = {k: (v if v != "" else None) for k, v in row.items()}
            try:
                ticket = Ticket.model_validate(cleaned)
                summary.valid_tickets.append(ticket)
                logger.info("Row %d valid (ticket_id=%s)", row_num, ticket.ticket_id)
            except ValidationError as exc:
                msg = exc.errors()[0]["msg"]
                summary.errors.append((row_num, msg))
                logger.error("Row %d invalid: %s", row_num, msg)

    return summary
