from pathlib import Path
import urllib.parse
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    ENV: str = "dev"
    DB_HOST: str = ""
    DB_PORT: int = 1433
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_WRITE_USER: str = ""
    DB_WRITE_PASSWORD: str = ""
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_ENCRYPT: str = "yes"
    DB_TRUST_SERVER_CERT: str = "yes"
    DB_CONNECT_TIMEOUT_SECONDS: int = 15
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE_SECONDS: int = 1800

    QUERY_TIMEOUT_SEC: int = 30
    ROW_CAP: int = 1000
    CONFIG_CACHE_TTL_SEC: int = 60
    ENABLE_WRITES: bool = False
    ENABLE_DELETE: bool = False
    EDIT_LOCK_FIELD: str = "docflow_seq"
    EDIT_LOCK_VALUE: int = 0

    JWT_PRIVATE_KEY_PATH: str = "./keys/jwt_private.pem"
    JWT_PUBLIC_KEY_PATH: str = "./keys/jwt_public.pem"
    JWT_ACCESS_TTL_MIN: int = 30
    JWT_REFRESH_TTL_DAYS: int = 14
    CORS_ORIGINS: str = ""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

def get_sqlalchemy_database_url(current_settings: Settings, user: str, password: str) -> str:
    encrypt = "yes" if current_settings.DB_ENCRYPT.lower() in ("yes", "true", "1") else "no"
    trust_cert = "yes" if current_settings.DB_TRUST_SERVER_CERT.lower() in ("yes", "true", "1") else "no"
    odbc_conn_str = f"DRIVER={current_settings.DB_DRIVER};SERVER={current_settings.DB_HOST},{current_settings.DB_PORT};DATABASE={current_settings.DB_NAME};UID={user};PWD={password};Encrypt={encrypt};TrustServerCertificate={trust_cert}"
    quoted = urllib.parse.quote_plus(odbc_conn_str)
    return f"mssql+pyodbc:///?odbc_connect={quoted}"
