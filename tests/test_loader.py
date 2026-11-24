from pathlib import Path
from tickets.loader import load_tickets_csv
from tickets.models import Priority, TicketStatus

HEADER = "ticket_id,customer_name,issue_summary,priority,status,created_date\n"


def test_valid_row(tmp_path: Path) -> None:
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text(
        HEADER + "101,Acme Corp,Server fan noise,HIGH,OPEN,2026-11-20\n",
        encoding="utf-8",
    )
    result = load_tickets_csv(csv_file)
    assert len(result.valid_tickets) == 1
    assert len(result.errors) == 0
    assert result.valid_tickets[0].priority == Priority.HIGH
    assert result.valid_tickets[0].status == TicketStatus.OPEN


def test_missing_field(tmp_path: Path) -> None:
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text(
        HEADER + "102,,Router offline,CRITICAL,OPEN,2026-11-20\n",
        encoding="utf-8",
    )
    result = load_tickets_csv(csv_file)
    assert len(result.valid_tickets) == 0
    assert len(result.errors) == 1
    assert result.errors[0][0] == 2


def test_bad_date(tmp_path: Path) -> None:
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text(
        HEADER + "103,Beta Ltd,VPN timeout,MEDIUM,IN_PROGRESS,20-11-2026\n",
        encoding="utf-8",
    )
    result = load_tickets_csv(csv_file)
    assert len(result.valid_tickets) == 0
    assert len(result.errors) == 1


def test_bad_enum(tmp_path: Path) -> None:
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text(
        HEADER + "104,Gamma Inc,Disk full,URGENT_ASAP,OPEN,2026-11-20\n",
        encoding="utf-8",
    )
    result = load_tickets_csv(csv_file)
    assert len(result.valid_tickets) == 0
    assert len(result.errors) == 1


def test_empty_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("", encoding="utf-8")
    result = load_tickets_csv(csv_file)
    assert len(result.valid_tickets) == 0
    assert len(result.errors) == 0
