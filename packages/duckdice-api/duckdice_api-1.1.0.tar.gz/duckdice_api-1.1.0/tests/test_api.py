import pytest
import requests
from unittest.mock import Mock, patch
from duckdice_api.client import DuckDiceAPI, DuckDiceConfig
from duckdice_api.models import UserInfo, CurrencyStats, PlayResponse, BalanceInfo, WageringBonus, Bet
from duckdice_api.exceptions import (
    DuckDiceError,
    AuthenticationError,
    HTTPError,
    NetworkError,
    ValidationError,
)


@pytest.fixture
def config():
    return DuckDiceConfig(api_key="test_key")


@pytest.fixture
def client(config):
    return DuckDiceAPI(config)


class TestDuckDiceModels:
    def test_balance_info_from_dict(self):
        data = {"currency": "BTC", "main": "1.0", "faucet": "0.1", "bonus": "0.01"}
        bal = BalanceInfo.from_dict(data)
        assert bal.currency == "BTC"
        assert bal.main == "1.0"
        assert bal.faucet == "0.1"

    def test_wagering_bonus_from_dict(self):
        data = {
            "name": "B1",
            "type": "deposit",
            "hash": "h1",
            "status": "active",
            "symbol": "BTC",
            "margin": "0.05",
        }
        bonus = WageringBonus.from_dict(data)
        assert bonus.name == "B1"
        assert bonus.margin == "0.05"

    def test_user_info_from_dict(self):
        data = {
            "hash": "uhash",
            "username": "user1",
            "createdAt": 12345,
            "level": 5,
            "balances": [{"currency": "BTC", "main": "1.0"}],
            "wageringBonuses": [],
            "tle": ["tle1"],
        }
        user = UserInfo.from_dict(data)
        assert user.username == "user1"
        assert len(user.balances) == 1
        assert user.tle == ["tle1"]

    def test_currency_stats_from_dict(self):
        data = {
            "bets": 100,
            "wins": 50,
            "profit": "1.5",
            "volume": "10.0",
            "balances": {"main": "1.0", "faucet": "0.5"},
        }
        stats = CurrencyStats.from_dict(data)
        assert stats.bets == 100
        assert stats.main_balance == "1.0"

    def test_bet_from_dict(self):
        data = {
            "hash": "bhash",
            "symbol": "BTC",
            "result": True,
            "choice": "High",
            "number": 5000,
            "chance": 49.5,
            "payout": 2.0,
            "betAmount": "1.0",
            "winAmount": "2.0",
            "profit": "1.0",
            "nonce": 1,
            "created": 12345,
            "gameMode": "main",
            "game": {"some": "meta"},
        }
        bet = Bet.from_dict(data)
        assert bet.hash == "bhash"
        assert bet.result is True
        assert bet.game_metadata == {"some": "meta"}

    def test_play_response_from_dict(self):
        data = {
            "bet": {"hash": "bhash", "result": True},
            "user": {"username": "user1"},
            "isJackpot": True,
            "jackpot": {"amount": "100"},
        }
        resp = PlayResponse.from_dict(data)
        assert resp.bet.hash == "bhash"
        assert resp.user.username == "user1"
        assert resp.is_jackpot is True
        assert resp.jackpot_amount == "100"


class TestDuckDiceAPI:
    @patch("duckdice_api.client.requests.Session.request")
    def test_request_success(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"key": "value"}
        mock_request.return_value = mock_resp

        result = client._request("GET", "/test")
        assert result == {"key": "value"}
        mock_request.assert_called_once()

    @patch("duckdice_api.client.requests.Session.request")
    def test_request_network_error(self, mock_request, client):
        mock_request.side_effect = requests.RequestException("conn error")
        with pytest.raises(NetworkError):
            client._request("GET", "/test")

    @patch("duckdice_api.client.requests.Session.request")
    def test_request_auth_error(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = False
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": "unauthorized"}
        mock_request.return_value = mock_resp

        with pytest.raises(AuthenticationError):
            client._request("GET", "/test")

    @patch("duckdice_api.client.requests.Session.request")
    def test_request_http_error(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        mock_resp.text = "internal error"
        mock_request.return_value = mock_resp

        with pytest.raises(HTTPError):
            client._request("GET", "/test")

    @patch("duckdice_api.client.requests.Session.request")
    def test_get_user_info(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"username": "tester"}
        mock_request.return_value = mock_resp

        user = client.get_user_info()
        assert isinstance(user, UserInfo)
        assert user.username == "tester"

    @patch("duckdice_api.client.requests.Session.request")
    def test_get_currency_stats(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"bets": 10}
        mock_request.return_value = mock_resp

        stats = client.get_currency_stats("BTC")
        assert isinstance(stats, CurrencyStats)
        assert stats.bets == 10

    @patch("duckdice_api.client.DuckDiceAPI.get_currency_stats")
    def test_get_faucet_balance(self, mock_stats, client):
        mock_stats.return_value = Mock(faucet_balance="0.5")
        assert client.get_faucet_balance("BTC") == "0.5"

    def test_prepare_bet_payload_validation(self, client):
        with pytest.raises(ValidationError):
            client._prepare_bet_payload("", "1.0")
        with pytest.raises(ValidationError):
            client._prepare_bet_payload("BTC", "")

    @patch("duckdice_api.client.requests.Session.request")
    def test_request_json_decode_error_in_error(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = False
        mock_resp.status_code = 400
        mock_resp.json.side_effect = Exception("not json")
        mock_resp.text = "plain error"
        mock_request.return_value = mock_resp

        with pytest.raises(HTTPError) as exc:
            client._request("GET", "/test")
        assert "plain error" in str(exc.value)

    @patch("duckdice_api.client.requests.Session.request")
    def test_request_json_decode_error_in_success(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.side_effect = ValueError("not json")
        mock_resp.text = "plain success"
        mock_request.return_value = mock_resp

        result = client._request("GET", "/test")
        assert result == "plain success"

    def test_prepare_bet_payload_all_params(self, client):
        payload = client._prepare_bet_payload(
            "btc", "1.0", user_wagering_bonus_hash="b1", faucet=True, tle_hash="t1"
        )
        assert payload["symbol"] == "BTC"
        assert payload["userWageringBonusHash"] == "b1"
        assert payload["faucet"] is True
        assert payload["tleHash"] == "t1"

    @patch("duckdice_api.client.requests.Session.request")
    def test_play_dice(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"bet": {"hash": "h"}}
        mock_request.return_value = mock_resp

        resp = client.play_dice("BTC", "1.0", "49.5", True)
        assert isinstance(resp, PlayResponse)
        assert resp.bet.hash == "h"

    @patch("duckdice_api.client.requests.Session.request")
    def test_play_range_dice(self, mock_request, client):
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"bet": {"hash": "h"}}
        mock_request.return_value = mock_resp

        resp = client.play_range_dice("BTC", "1.0", [0, 5000], True)
        assert isinstance(resp, PlayResponse)
        assert resp.bet.hash == "h"

    def test_play_range_dice_validation(self, client):
        with pytest.raises(ValidationError):
            client.play_range_dice("BTC", "1.0", [0], True)

def test_api_reexports():
    from duckdice_api.api import DuckDiceAPI, DuckDiceConfig, DuckDiceAPIException
    assert DuckDiceAPI is not None
    assert DuckDiceConfig is not None
    assert DuckDiceAPIException is not None
