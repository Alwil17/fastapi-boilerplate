from unittest.mock import patch

from fastapi.testclient import TestClient


def test_engine_disposed_on_shutdown(client):
    from app.main import app

    with patch("app.main.engine") as mock_engine:
        with TestClient(app):
            mock_engine.dispose.assert_not_called()
        mock_engine.dispose.assert_called_once()
