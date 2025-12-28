import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue


def setup_logging_pipeline(
    db_handler: logging.Handler,
    db_enabled: bool,
    db_level: str,
    console_enabled: bool,
    console_level: str,
):
    """
    Set up the shared queue → listener → DB pipeline plus optional console.
    Returns (log_queue, listener, root_logger).
    """
    log_queue: Queue = Queue()

    handlers: list[logging.Handler] = []

    if db_enabled:
        db_handler.setLevel(getattr(logging, db_level.upper()))
        handlers.append(db_handler)

    listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
    listener.start()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(queue_handler)

    if console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, console_level.upper()))
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(console_handler)

    return log_queue, listener, root_logger
