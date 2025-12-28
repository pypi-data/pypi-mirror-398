import json
import logging
import time
import zlib

from sqlalchemy.orm import Session

from . import dates
from .db import LogRecord


class SQLAlchemyHandler(logging.Handler):
    """
    Handler that writes LogRecord objects to SQLite via SQLAlchemy.
    Runs behind a QueueListener in a dedicated thread.
    """

    _STANDARD_ATTRS = frozenset(
        [
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        ]
    )

    def __init__(
        self,
        engine,
        max_retries=5,
        base_backoff=0.1,
        max_backoff=1.0,
        fallback_path="log_fallback.txt",
    ):
        super().__init__()
        self.engine = engine
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.fallback_path = fallback_path

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)

            exc_text = None
            if record.exc_info:
                if self.formatter and hasattr(self.formatter, "formatException"):
                    exc_text = self.formatter.formatException(record.exc_info)
                else:
                    exc_text = logging.Formatter().formatException(record.exc_info)

            ts_julian = dates.unix_to_julian(record.created)

            extra_data = {}
            for key, value in record.__dict__.items():
                if key not in self._STANDARD_ATTRS and not key.startswith("_"):
                    extra_data[key] = value

            extra_blob = None
            if extra_data:
                try:
                    json_bytes = json.dumps(
                        extra_data,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                    extra_blob = zlib.compress(json_bytes)
                except Exception:
                    self._write_fallback(
                        record,
                        RuntimeError("Failed to serialize extra data to JSON"),
                    )
                    extra_blob = None

            orm_entry = LogRecord(
                timestamp_julian=ts_julian,
                level=record.levelname,
                logger_name=record.name,
                message=msg,
                module=record.name,
                function=record.funcName,
                line_number=record.lineno,
                exception=exc_text,
                extra=extra_blob,
            )

            self._insert_with_retry(orm_entry, record)
        except Exception:
            self.handleError(record)

    def _insert_with_retry(
        self,
        orm_entry: LogRecord,
        original_record: logging.LogRecord,
    ) -> None:
        attempts = 0
        while True:
            try:
                with Session(self.engine) as session:
                    session.add(orm_entry)
                    session.commit()
                return
            except Exception as exc:
                msg = str(exc).lower()
                locked = any(
                    s in msg
                    for s in [
                        "database is locked",
                        "database locked",
                        "database is busy",
                        "database busy",
                    ]
                )

                attempts += 1

                if locked and attempts <= self.max_retries:
                    delay = min(
                        self.base_backoff * (2 ** (attempts - 1)),
                        self.max_backoff,
                    )
                    time.sleep(delay)
                    continue

                self._write_fallback(original_record, exc)
                self.handleError(original_record)
                return

    def _write_fallback(self, record: logging.LogRecord, exc: Exception) -> None:
        try:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
            with open(self.fallback_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{ts}] {record.levelname} {record.name}: "
                    f"{record.getMessage()} (logging failure: {exc})\n"
                )
        except Exception:
            # No further logging; avoid recursion
            pass
