from routers.debug import root, health_check


def test_root_endpoint_function():
    payload = root()
    assert payload["status"] == "running"
    assert payload["message"] == "Clyvara Backend API"


def test_health_endpoint_function(monkeypatch):
    import database

    monkeypatch.setattr(database, "test_connection", lambda: True)
    payload = health_check()
    assert payload["status"] == "healthy"
    assert payload["database"] == "connected"
