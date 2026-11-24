import json
import logging

from pathlib import Path
from datetime import datetime, timezone


PROJECT_DIR = Path(__file__).resolve().parent

LOG_DIR = PROJECT_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "orchestrator.jsonl"


class JSONLogFormatter(logging.Formatter):

    def format(self, record):

        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                timezone.utc
            ).isoformat(),

            "level": record.levelname,

            "logger": record.name,

            "message": record.getMessage(),

            "agent": getattr(
                record, "agent", None
            ),

            "event": getattr(
                record, "event", None
            ),

            "data": getattr(
                record, "data", {}
            )
        }

        if record.exc_info:

            log_entry["exception"] = (
                self.formatException(record.exc_info)
            )

        return json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str
        )


def get_logger():

    logger = logging.getLogger(
        "ai_api_orchestrator"
    )

    logger.setLevel(logging.DEBUG)

    logger.propagate = False

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()

    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    file_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(
        JSONLogFormatter()
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = get_logger()


def log_event(
    level,
    message,
    agent=None,
    event=None,
    **data
):

    logger.log(
        level,
        message,
        extra={
            "agent": agent,
            "event": event,
            "data": data
        }
    )
