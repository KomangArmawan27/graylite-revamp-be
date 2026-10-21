from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings, get_sqlalchemy_database_url


def _make_engine(user: str, password: str):
    db_url = get_sqlalchemy_database_url(settings, user=user, password=password)
    return create_engine(
        db_url,
        connect_args={"timeout": settings.DB_CONNECT_TIMEOUT_SECONDS},
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
        execution_options={"fast_executemany": True},
    )

engine = _make_engine(settings.DB_USER, settings.DB_PASSWORD)
engine_write = _make_engine(
    settings.DB_WRITE_USER or settings.DB_USER,
    settings.DB_WRITE_PASSWORD or settings.DB_PASSWORD,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
SessionWrite = sessionmaker(bind=engine_write, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        try:
            db.connection().exec_driver_sql(f"SET LOCK_TIMEOUT {settings.QUERY_TIMEOUT_SEC * 1000}")
        except Exception:
            pass
        yield db
    finally:
        db.close()


def get_db_write():
    if not settings.ENABLE_WRITES:
        from app.core.errors import AppError
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    db = SessionWrite()
    try:
        try:
            db.connection().exec_driver_sql(f"SET LOCK_TIMEOUT {settings.QUERY_TIMEOUT_SEC * 1000}")
        except Exception:
            pass
        yield db
    finally:
        db.close()
