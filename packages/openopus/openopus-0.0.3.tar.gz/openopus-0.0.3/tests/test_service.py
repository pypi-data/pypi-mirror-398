import pytest
from unittest.mock import Mock
from openopus.service import OpenOpus
from openopus.models import Composer, Work


class DummyCache:
    """Very small cache used only for unit‑tests"""

    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value):
        self._store[key] = value


@pytest.fixture
def mock_client(monkeypatch):
    mock = Mock(name="OpenOpusClientMock")
    monkeypatch.setattr("openopus.service.OpenOpusClient", lambda *a, **kw: mock)
    return mock


def test_list_composeres_cache(mock_client):
    mock_client.list_composers.return_value = {
        "composers": [
            {"id": "1", "complete_name": "Johann Sebastian Bach", "birth": "1685", "death": "1750", "epoch": "Baroque",
             "portrait": ""}]
    }
    svc = OpenOpus(cache=DummyCache())
    composers1 = svc.composers()
    composers2 = svc.composers()  # Should use cache

    assert composers1[0].name == "Johann Sebastian Bach"
    assert composers1 == composers2
    assert mock_client.list_composers.call_count == 1


def test_works_for_composer(mock_client):
    mock_client.works_by_composer.return_value = {
        "works": [{"id": "10", "title": "Goldberg Variations, BWV.988", "genre": "Keyboard"}]
    }
    svc = OpenOpus(cache=DummyCache())
    works = svc.works(1)
    assert works[0].title == "Goldberg Variations, BWV.988"
