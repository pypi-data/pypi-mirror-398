import pytest
from unittest.mock import Mock, patch

from openopus.errors import OpenOpusError
from openopus.client import OpenOpusClient


def test_get_success():
    client = OpenOpusClient()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"composers": []}

    with patch("requests.get", return_value=mock_response):
        data = client.get("/composer/list/search/.json")
        assert data == {"composers": []}


def test_get_failure_raises_error():
    client = OpenOpusClient()
    mock_response = Mock()
    mock_response.status_code = 500

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(OpenOpusError):
            client.get("/composer/list/search/.json")
