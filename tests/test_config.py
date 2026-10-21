from app.core.config import settings

def test_settings_loaded():
    assert settings.DB_PORT == 1433
