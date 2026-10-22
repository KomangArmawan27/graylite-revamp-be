import pytest
from app.modules.menu.service import should_exclude

def test_exclusion_patterns():
    assert should_exclude("Browser.Sales.Order.Tidak Dipakai") is True
    assert should_exclude("Browser.Sales.Order.260416") is True
    assert should_exclude("Browser.Sales.Order.Dev.260107") is True
    assert should_exclude("Browser.Sales.Order.Retail") is False
    assert should_exclude(" Browser.Sales.Order.Retail ") is False
