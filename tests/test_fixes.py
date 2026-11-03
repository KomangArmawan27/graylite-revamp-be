from decimal import Decimal
from datetime import date, datetime
from app.shared.types import clean_caption, serialize_row, normalize_type
from app.shared.expr.evaluator import evaluate_expression

def test_clean_caption():
    assert clean_caption("Item AccInv<br/>Monitor") == "Item AccInv Monitor"
    assert clean_caption("<b>Sales Order</b>") == "Sales Order"
    assert clean_caption("   Spaces   ") == "Spaces"
    assert clean_caption(None) == ""

def test_serialize_row_decimals():
    row = {
        "doc_discfactor": Decimal("0E-17"),
        "total": Decimal("1E+2"),
        "negative": Decimal("-0.0000"),
        "val": 123,
    }
    serialized = serialize_row(row)
    assert serialized["doc_discfactor"] == "0.00000000000000000"
    assert serialized["total"] == "100"
    assert serialized["negative"] == "-0.0000"
    assert serialized["val"] == 123

def test_normalize_type_variations():
    assert normalize_type("integer", "int", "doc_id", 0) == "integer"
    assert normalize_type("number", "decimal", "trans_qty", 2) == "number"
    assert normalize_type(None, "date", "doc_date", 0) == "date"

def test_expression_now_and_dateadd():
    context = {}
    res = evaluate_expression("NOW()", context)
    assert isinstance(res, datetime)

    res_date = evaluate_expression("DATEADD(-360, TODAY())", context)
    assert isinstance(res_date, date)
