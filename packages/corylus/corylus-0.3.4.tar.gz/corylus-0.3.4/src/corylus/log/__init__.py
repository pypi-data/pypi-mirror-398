__all__ = ["getLogger", "logs"]

import atexit
import logging
from threading import Lock

from . import config as _config
from . import db as _db
from . import handler as _handler
from . import queueing as _queueing
from . import query as _query

_initialized = False
_init_lock = Lock()

_engine = None
_LogRecordModel = None
_db_handler = None
_listener = None
_log_queue = None
_root_logger = None


def _initialize_logging():
    global _initialized, _engine, _LogRecordModel
    global _db_handler, _listener, _log_queue, _root_logger

    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        # 1. Engine + ORM model
        engine = _db.create_engine()
        _engine = engine
        _LogRecordModel = _db.LogRecord

        # 2. Handler instance
        db_handler = _handler.SQLAlchemyHandler(
            engine=engine,
            max_retries=_config.DB_MAX_RETRIES,
            base_backoff=_config.DB_BASE_BACKOFF,
            max_backoff=_config.DB_MAX_BACKOFF,
            fallback_path=_config.DB_FALLBACK_PATH,
        )
        db_handler.setFormatter(logging.Formatter("%(message)s"))
        _db_handler = db_handler

        # 3. Queue + listener + root logger
        (
            log_queue,
            listener,
            root_logger,
        ) = _queueing.setup_logging_pipeline(
            db_handler=db_handler,
            db_enabled=_config.DB_ENABLED,
            db_level=_config.DB_LEVEL,
            console_enabled=_config.CONSOLE_ENABLED,
            console_level=_config.CONSOLE_LEVEL,
        )

        _log_queue = log_queue
        _listener = listener
        _root_logger = root_logger

        # 4. Shutdown hook
        def _shutdown_logging():
            try:
                listener.stop()
            except Exception:
                pass

            for h in list(root_logger.handlers):
                try:
                    h.flush()
                except Exception:
                    pass
                try:
                    h.close()
                except Exception:
                    pass

        atexit.register(_shutdown_logging)

        _initialized = True


def logs(*date_filter, db: str | None = None):
    """
    Public wrapper that exposes the log iterator.

    Args:
        db: Optional alternate log database. If it contains '://', it is treated
            as a SQLAlchemy URL. Otherwise it is treated as a filesystem path
            and converted to a SQLite URL.
    """
    _initialize_logging()

    engine = _db.create_engine_from_url(db if "://" in db else f"sqlite:///{db}") if db else _engine

    return _query.iter_logs(engine, _LogRecordModel, *date_filter)


def getLogger(name: str) -> logging.Logger:
    """
    Return a standard logging.Logger with the given name, configured
    with the shared queue → DB pipeline and optional console output.
    """
    _initialize_logging()
    return logging.getLogger(name)
