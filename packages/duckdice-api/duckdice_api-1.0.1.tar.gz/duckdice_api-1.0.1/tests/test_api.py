"""Unit tests for DuckDice API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from duckdice_api import DuckDiceAPI, DuckDiceConfig, DuckDiceAPIException


@pytest.fixture
def config():
    """Create a test config."""
    return DuckDiceConfig(api_key="test_key_123")


@pytest.fixture
def client(config):
    """Create a test client."""
    return DuckDiceAPI(config)


class TestDuckDiceConfig:
    """Tests for DuckDiceConfig dataclass."""

    def test_config_init_required_field(self):
        """Test config requires api_key."""
        cfg = DuckDiceConfig(api_key="my_key")
        assert cfg.api_key == "my_key"
        assert cfg.base_url == "https://duckdice.io/api"
        assert cfg.timeout == 30

    def test_config_init_custom_values(self):
        """Test config with custom values."""
        cfg = DuckDiceConfig(api_key="my_key", base_url="http://localhost/api", timeout=60)
        assert cfg.api_key == "my_key"
        assert cfg.base_url == "http://localhost/api"
        assert cfg.timeout == 60


class TestDuckDiceAPI:
    """Tests for DuckDiceAPI client."""

    def test_client_init(self, client):
        """Test client initialization."""
        assert client.config.api_key == "test_key_123"
        assert client.session is not None
        assert client.session.headers.get("User-Agent") == "DuckDiceBot/1.0.0"

    @patch("duckdice_api.api.requests.Session.request")
    def test_play_dice_success(self, mock_request, client):
        """Test successful play_dice call."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "bet": {"hash": "bb7bd4178d9", "result": True},
            "user": {"balance": "69.23"}
        }
        mock_request.return_value = mock_response

        result = client.play_dice(symbol="XLM", amount="0.1", chance="77.77", is_high=True)

        assert result["bet"]["hash"] == "bb7bd4178d9"
        assert result["bet"]["result"] is True
        assert result["user"]["balance"] == "69.23"
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "api_key" in call_args.kwargs["params"]

    @patch("duckdice_api.api.requests.Session.request")
    def test_play_dice_with_optional_params(self, mock_request, client):
        """Test play_dice with optional parameters."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"bet": {}}
        mock_request.return_value = mock_response

        result = client.play_dice(
            symbol="XLM",
            amount="0.1",
            chance="77.77",
            is_high=True,
            user_wagering_bonus_hash="bonus123",
            faucet=False,
            tle_hash="tle456"
        )

        assert result == {"bet": {}}
        call_json = mock_request.call_args.kwargs["json"]
        assert call_json["userWageringBonusHash"] == "bonus123"
        assert call_json["faucet"] is False
        assert call_json["tleHash"] == "tle456"

    @patch("duckdice_api.api.requests.Session.request")
    def test_play_range_dice_success(self, mock_request, client):
        """Test successful play_range_dice call."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "bet": {"hash": "abc123", "choice": "In"},
            "user": {"balance": "50.00"}
        }
        mock_request.return_value = mock_response

        result = client.play_range_dice(symbol="XLM", amount="0.1", range_vals=[0, 5000], is_in=True)

        assert result["bet"]["hash"] == "abc123"
        assert result["bet"]["choice"] == "In"
        call_json = mock_request.call_args.kwargs["json"]
        assert call_json["range"] == [0, 5000]
        assert call_json["isIn"] is True

    @patch("duckdice_api.api.requests.Session.request")
    def test_get_currency_stats(self, mock_request, client):
        """Test get_currency_stats."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "bets": 100,
            "wins": 50,
            "profit": "373.03978203",
            "volume": "77284.31558445",
            "balances": {"main": "0.0012", "faucet": "0"}
        }
        mock_request.return_value = mock_response

        result = client.get_currency_stats("XLM")

        assert result["bets"] == 100
        assert result["wins"] == 50
        assert result["profit"] == "373.03978203"
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "/api/bot/stats/XLM" in call_args[0][1]

    @patch("duckdice_api.api.requests.Session.request")
    def test_get_user_info(self, mock_request, client):
        """Test get_user_info."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "hash": "d6f7a12ab5",
            "username": "DuckDiceBot",
            "level": 5,
            "balance": "69.23",
            "wagered": [{"currency": "BTC", "amount": "14.24675424"}],
            "balances": [{"currency": "BTC", "main": "0.00001"}]
        }
        mock_request.return_value = mock_response

        result = client.get_user_info()

        assert result["username"] == "DuckDiceBot"
        assert result["level"] == 5
        assert len(result["wagered"]) > 0
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "/api/bot/user-info" in call_args[0][1]

    @patch("duckdice_api.api.requests.Session.request")
    def test_api_error_response(self, mock_request, client):
        """Test API error response handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_request.return_value = mock_response

        with pytest.raises(DuckDiceAPIException) as exc_info:
            client.play_dice(symbol="XLM", amount="0.1", chance="77.77", is_high=True)

        assert "400" in str(exc_info.value)
        assert "Invalid request" in str(exc_info.value)

    @patch("duckdice_api.api.requests.Session.request")
    def test_api_error_network(self, mock_request, client):
        """Test network error handling."""
        import requests
        mock_request.side_effect = requests.RequestException("Connection timeout")

        with pytest.raises(DuckDiceAPIException) as exc_info:
            client.get_user_info()

        assert "request failed" in str(exc_info.value)

    @patch("duckdice_api.api.requests.Session.request")
    def test_api_response_non_json(self, mock_request, client):
        """Test non-JSON response handling."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Plain text response"
        mock_request.return_value = mock_response

        result = client.get_user_info()
        assert result == "Plain text response"

    @patch("duckdice_api.api.requests.Session.request")
    def test_play_dice_is_high_boolean_coercion(self, mock_request, client):
        """Test is_high is properly coerced to boolean."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"bet": {}}
        mock_request.return_value = mock_response

        client.play_dice(symbol="XLM", amount="0.1", chance="77.77", is_high=1)

        call_json = mock_request.call_args.kwargs["json"]
        assert call_json["isHigh"] is True
        assert isinstance(call_json["isHigh"], bool)

    @patch("duckdice_api.api.requests.Session.request")
    def test_api_key_always_included(self, mock_request, client):
        """Test API key is always added to params."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        client.get_user_info()

        call_params = mock_request.call_args.kwargs["params"]
        assert call_params["api_key"] == "test_key_123"
