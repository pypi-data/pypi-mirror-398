import datetime
import json
import logging
import zlib

from sqlalchemy.orm import Session

from . import dates


def _day_range_julian(d: datetime.date | datetime.datetime):
    if isinstance(d, datetime.datetime):
        d = d.date()
    start_dt = datetime.datetime(d.year, d.month, d.day, 0, 0, 0)
    end_dt = start_dt + datetime.timedelta(days=1)
    return (
        dates.unix_to_julian(start_dt.timestamp()),
        dates.unix_to_julian(end_dt.timestamp()),
    )


def iter_logs(engine, LogRecordModel, *date_filter):
    """
    Core implementation for `corylus.log.logs`.

    `date_filter` follows the same rules as the original implementation.
    """
    try:
        start_julian = None
        end_julian = None

        match date_filter:
            case ["today"]:
                today = datetime.datetime.now().date()
                start_julian, end_julian = _day_range_julian(today)
            case ["yesterday"]:
                yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
                start_julian, end_julian = _day_range_julian(yesterday)
            case [dt]:
                start_julian, end_julian = _day_range_julian(dt)
            case [start, end]:
                start_julian, _ = _day_range_julian(start)
                _, end_julian = _day_range_julian(end)
            case []:
                # No filter: return everything
                pass
            case _:
                raise ValueError(f"Invalid date_filter: {date_filter!r}")

        with Session(engine) as session:
            query = session.query(LogRecordModel).order_by(
                LogRecordModel.timestamp_julian.desc()
            )

            if start_julian is not None:
                query = query.filter(LogRecordModel.timestamp_julian >= start_julian)
            if end_julian is not None:
                query = query.filter(LogRecordModel.timestamp_julian < end_julian)

            for log_record in query:
                log_dict = {
                    "id": log_record.id,
                    "timestamp_julian": log_record.timestamp_julian,
                    "level": log_record.level,
                    "logger_name": log_record.logger_name,
                    "message": log_record.message,
                    "module": log_record.module,
                    "function": log_record.function,
                    "line_number": log_record.line_number,
                    "exception": log_record.exception,
                    "extra": None,
                }

                if log_record.extra:
                    try:
                        decompressed = zlib.decompress(log_record.extra)
                        log_dict["extra"] = json.loads(decompressed.decode("utf-8"))
                    except (zlib.error, json.JSONDecodeError) as e:
                        logging.getLogger(__name__).error(
                            f"Extra data decompression failed for record "
                            f"{log_record.id}: {e}"
                        )

                yield log_dict

    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Log iteration failed: {e}")
