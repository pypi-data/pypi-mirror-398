import logging

from sqlalchemy import (
    Column,
    Float,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine as sa_create_engine,
    event,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from . import config

Base = declarative_base()


class LogRecord(Base):
    __tablename__ = "log_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp_julian = Column(Float, nullable=False, index=True)

    level = Column(String(10), nullable=False, index=True)
    logger_name = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(255), index=True)
    function = Column(String(255))
    line_number = Column(Integer)
    exception = Column(Text)

    extra = Column(LargeBinary)  # compressed JSON blob


def create_engine():
    engine = _create_engine()
    _apply_sqlite_pragmas(engine)
    Base.metadata.create_all(engine)
    return engine


def create_engine_from_url(db_url: str):
    engine = _create_engine(db_url)
    _apply_sqlite_pragmas(engine)
    # Important: don't call Base.metadata.create_all(engine) here;
    # a typo in a path would silently create a new empty DB file.
    return engine


def _create_engine(db_url: str | None = None):
    return sa_create_engine(
        db_url or config.SQLITE_DB_URL,
        echo=False,
        poolclass=NullPool,
        connect_args={
            "timeout": config.SQLITE_TIMEOUT_SECONDS,
            "check_same_thread": False,
        },
    )


def _apply_sqlite_pragmas(engine):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
