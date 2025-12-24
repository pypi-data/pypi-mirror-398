import pytest


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):

    monkeypatch.setenv("URL_PREFIX", "/api")
    monkeypatch.setenv("API_SECRET_NAME", "test/secret")
    monkeypatch.setenv("DETAIL_INFORMATION_ENDPOINT",
                       "https://api.example.com/det")
    monkeypatch.setenv("BASIC_INFORMATION_ENDPOINT",
                       "https://api.example.com/bas")
    monkeypatch.setenv("IDENTIFICATION_BY_KEY_ENDPOINT",
                       "https://api.example.com/i")
    monkeypatch.setenv("KEYS_BY_IDENTIFICATION_ENDPOINT",
                       "https://api.example.com/k")
    yield
