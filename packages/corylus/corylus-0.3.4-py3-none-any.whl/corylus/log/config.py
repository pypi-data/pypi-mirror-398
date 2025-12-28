from os.path import expanduser
import tempfile
from inceptum import config as _cfg

# Database configuration
SQLITE_DB_URL = f'sqlite:///{expanduser(_cfg("corylus.log.db.path", default=f"/{tempfile.gettempdir()}/logs.db"))}'
SQLITE_TIMEOUT_SECONDS = 30.0

DB_MAX_RETRIES = 5
DB_BASE_BACKOFF = 0.1
DB_MAX_BACKOFF = 1.0
DB_FALLBACK_PATH = "log_fallback.txt"

# DB handler configuration
DB_ENABLED = _cfg("corylus.log.db.enabled", default=True)
DB_LEVEL = _cfg("corylus.log.db.level", default="INFO")

# Console configuration
CONSOLE_ENABLED = _cfg("corylus.log.console.enabled", default=True)
CONSOLE_LEVEL = _cfg("corylus.log.console.level", default="INFO")
