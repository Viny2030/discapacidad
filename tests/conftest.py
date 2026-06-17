"""
conftest.py
Fixtures compartidos para todos los tests del Observatorio de Discapacidad.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP de prueba — reutilizado en toda la sesión."""
    with TestClient(app) as c:
        yield c