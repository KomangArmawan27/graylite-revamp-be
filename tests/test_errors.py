from sqlalchemy.exc import DBAPIError
from app.core.errors import (
    map_db_error,
    clean_raiserror_message,
    Conflict,
    ValidationFailed,
    RuleViolation,
    DbUnavailable,
    QueryTimeout,
)


class DummyOrig:
    def __init__(self, args):
        self.args = args


class DummyDBAPIError(DBAPIError):
    def __init__(self, message, sqlstate="42000"):
        self.orig = DummyOrig((sqlstate, message))
        super().__init__("SELECT 1", {}, Exception(message))


def test_clean_raiserror_message():
    raw = "[Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Custom business error occurred. (50000) (SQLExecDirectW)"
    cleaned = clean_raiserror_message(raw)
    assert cleaned == "Custom business error occurred."


def test_map_db_error_deadlock():
    err = DummyDBAPIError("[Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Deadlock encountered (1205)")
    mapped = map_db_error(err)
    assert isinstance(mapped, Conflict)
    assert mapped.code == "conflict"


def test_map_db_error_unique():
    err = DummyDBAPIError("[Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Violation of UNIQUE KEY constraint (2627)")
    mapped = map_db_error(err)
    assert isinstance(mapped, Conflict)


def test_map_db_error_not_null():
    err = DummyDBAPIError("[Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Cannot insert the value NULL into column 'doc_no' (515)")
    mapped = map_db_error(err)
    assert isinstance(mapped, ValidationFailed)
    assert mapped.details[0]["field"] == "doc_no"
    assert mapped.details[0]["code"] == "required"


def test_map_db_error_raiserror():
    err = DummyDBAPIError("[Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Invalid order status (50001)")
    mapped = map_db_error(err)
    assert isinstance(mapped, RuleViolation)
    assert mapped.message == "Invalid order status"


def test_map_db_error_timeout():
    err = DummyDBAPIError("Query timeout expired", sqlstate="HYT00")
    mapped = map_db_error(err)
    assert isinstance(mapped, QueryTimeout)


def test_map_db_error_unavailable():
    err = DummyDBAPIError("Communication link failure", sqlstate="08S01")
    mapped = map_db_error(err)
    assert isinstance(mapped, DbUnavailable)
