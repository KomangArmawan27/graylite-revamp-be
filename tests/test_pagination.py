import pytest
from app.core.pagination import (
    build_keyset_predicate,
    encode_cursor,
    decode_cursor,
    resolve_sort,
    escape_like_string,
    finish_page,
    make_fingerprint,
)
from app.core.errors import InvalidSort


def test_encode_decode_cursor():
    data = {"v": 1, "m": "keyset", "last": ["2026-10-20", 900101], "fp": "9b1c4e07"}
    cursor = encode_cursor(data)
    decoded = decode_cursor(cursor)
    assert decoded == data


def test_decode_invalid_cursor():
    assert decode_cursor(None) is None
    assert decode_cursor("not-base64!!!") is None
    bad_data = encode_cursor({"v": 2, "m": "keyset", "last": []})
    assert decode_cursor(bad_data) is None


def test_fingerprint():
    fp1 = make_fingerprint(1422, [("doc_date", "desc")], {"status": "1"}, "test", 1)
    fp2 = make_fingerprint(1422, [("doc_date", "desc")], {"status": "1"}, "test", 1)
    fp3 = make_fingerprint(1422, [("doc_date", "desc")], {"status": "2"}, "test", 1)
    assert fp1 == fp2
    assert fp1 != fp3


def test_resolve_sort():
    known = {"doc_date", "doc_no", "doc_id", "status"}
    res1 = resolve_sort(known, None, [("doc_date", "desc")], "doc_id")
    assert res1 == [("doc_date", "desc"), ("doc_id", "desc")]

    res2 = resolve_sort(known, "doc_no:asc", [("doc_date", "desc")], "doc_id")
    assert res2 == [("doc_no", "asc"), ("doc_id", "desc")]

    with pytest.raises(InvalidSort):
        resolve_sort(known, "unknown_col:asc", [("doc_date", "desc")], "doc_id")


def test_build_keyset_predicate():
    sort = [("doc_date", "desc"), ("doc_id", "desc")]
    sql, params = build_keyset_predicate(sort, ["2026-10-20", 900101])
    assert "doc_date" in sql
    assert "doc_id" in sql
    assert params == ["2026-10-20", "2026-10-20", 900101]

    sql_null, _params_null = build_keyset_predicate([("doc_date", "desc"), ("doc_id", "desc")], [None, 900101])
    assert "IS NULL" in sql_null

    sql_asc, params_asc = build_keyset_predicate([("doc_date", "asc"), ("doc_id", "asc")], ["2026-10-20", 900101])
    assert "> ?" in sql_asc
    assert params_asc == ["2026-10-20", "2026-10-20", 900101]


def test_escape_like_string():
    assert escape_like_string("test%_[]\\") == "test\\%\\_\\[]\\\\"


def test_finish_page():
    rows = [{"doc_id": i} for i in range(5)]
    page = finish_page(rows, 3, [("doc_id", "asc")], 1422, "12345678")
    assert page.pageSize == 3
    assert page.hasMore is True
    assert len(page.items) == 3
    assert page.nextCursor is not None

    page_exact = finish_page(rows[:3], 3, [("doc_id", "asc")], 1422, "12345678")
    assert page_exact.hasMore is False
    assert page_exact.nextCursor is None
