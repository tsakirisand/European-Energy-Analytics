import os
import subprocess
import time
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Environment variable parameters
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Fix legacy postgres:// URL format for SQLAlchemy compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    POSTGRES_URI = DATABASE_URL
    IS_REMOTE_DB = True
else:
    PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    PG_PORT = os.environ.get("POSTGRES_PORT", "5433")
    PG_USER = os.environ.get("POSTGRES_USER", "postgres")
    PG_PASS = os.environ.get("POSTGRES_PASSWORD", "")
    PG_DB = os.environ.get("POSTGRES_DB", "european_energy")
    
    auth_str = f"{PG_USER}:{PG_PASS}@" if PG_PASS else f"{PG_USER}@"
    POSTGRES_URI = f"postgresql://{auth_str}{PG_HOST}:{PG_PORT}/{PG_DB}"
    IS_REMOTE_DB = False

DB_NAME = os.environ.get("POSTGRES_DB", "european_energy")
PG_PORT = int(os.environ.get("POSTGRES_PORT", 5433))
PG_USER = os.environ.get("POSTGRES_USER", "postgres")
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "pgdata"))
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "postgres.log"))
SQLITE_URI = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), 'european_energy.db'))}"

_engine: Engine | None = None

def ensure_postgres_running() -> bool:
    """Ensure PostgreSQL connection works (remote or local cluster)."""
    if IS_REMOTE_DB:
        try:
            engine = create_engine(POSTGRES_URI, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"[DatabaseManager] Remote PostgreSQL connection error: {e}")
            return False

    # First test if local port is accepting connections
    try:
        engine = create_engine(f"postgresql://{PG_USER}@{PG_HOST}:{PG_PORT}/postgres", connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        pass

    # If not running, initialize cluster if needed and start pg_ctl
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(os.path.dirname(DATA_DIR), exist_ok=True)
            subprocess.run(["initdb", "-D", DATA_DIR, "-U", PG_USER, "--auth=trust"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        subprocess.run(
            ["pg_ctl", "-D", DATA_DIR, "-l", LOG_FILE, "-o", f"-p {PG_PORT}", "start"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(2)

        # Create database european_energy
        engine = create_engine(f"postgresql://{PG_USER}@{PG_HOST}:{PG_PORT}/postgres")
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f"CREATE DATABASE {DB_NAME};"))
        return True
    except Exception as e:
        print(f"[DatabaseManager] Local Postgres initialization note: {e}")
        return False

def get_db_engine() -> Engine:
    """Get or create SQLAlchemy engine. Uses PostgreSQL if available, SQLite as fallback."""
    global _engine
    if _engine is not None:
        return _engine

    if ensure_postgres_running():
        try:
            _engine = create_engine(POSTGRES_URI)
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return _engine
        except Exception as e:
            print(f"[DatabaseManager] Could not connect to Postgres DB '{DB_NAME}', creating it: {e}")
            try:
                admin_engine = create_engine(f"postgresql://{PG_USER}@{PG_HOST}:{PG_PORT}/postgres")
                with admin_engine.connect() as conn:
                    conn.execution_options(isolation_level="AUTOCOMMIT")
                    conn.execute(text(f"CREATE DATABASE {DB_NAME};"))
                _engine = create_engine(POSTGRES_URI)
                return _engine
            except Exception as e2:
                print(f"[DatabaseManager] Postgres setup fallback to SQLite: {e2}")

    # SQLite fallback for test environments where postgres binary is absent
    _engine = create_engine(SQLITE_URI)
    return _engine

def init_schema():
    """Apply the SQL schema migrations to the database."""
    engine = get_db_engine()
    schema_file = os.path.join(os.path.dirname(__file__), "schema", "001_init_schema.sql")
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found at {schema_file}")

    with open(schema_file, "r") as f:
        sql_script = f.read()

    # If SQLite, adjust AUTOINCREMENT and NUMERIC syntax compatibility
    if engine.dialect.name == "sqlite":
        sql_script = sql_script.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sql_script = sql_script.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        sql_script = sql_script.replace("NUMERIC(14, 4)", "REAL")
        sql_script = sql_script.replace("NUMERIC(10, 6)", "REAL")
        sql_script = sql_script.replace("NUMERIC(16, 2)", "REAL")
        sql_script = sql_script.replace("NUMERIC(6, 2)", "REAL")

    # Execute statements split by semicolon
    statements = [s.strip() for s in sql_script.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    print(f"[DatabaseManager] Schema successfully initialized on {engine.dialect.name.upper()} database.")

if __name__ == "__main__":
    init_schema()
