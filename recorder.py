import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data/rates")


def get_monthly_log_file(now: datetime) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"usd_idr_{now.strftime('%Y-%m')}.jsonl"
    return DATA_DIR / filename


def append_record(record: dict):
    now = datetime.now(timezone.utc).astimezone()
    log_file = get_monthly_log_file(now)

    with open(log_file, "a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")

    print(f"Record appended to {log_file}")
