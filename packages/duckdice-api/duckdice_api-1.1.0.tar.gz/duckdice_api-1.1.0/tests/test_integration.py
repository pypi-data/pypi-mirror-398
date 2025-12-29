import pytest
import time
from duckdice_api import DuckDiceAPI, DuckDiceConfig
from duckdice_api.exceptions import DuckDiceError

# Constants for integration testing
API_KEY = "8f9a51ce-af2d-11f0-a08a-524acb1a7d8c"
TEST_SYMBOL = "DOGE"
MIN_AMOUNT = "0.01"  # Increased based on 422 error

@pytest.fixture(scope="module")
def api_client():
    cfg = DuckDiceConfig(api_key=API_KEY)
    return DuckDiceAPI(cfg)

def test_integration_get_user_info(api_client):
    """Test retrieving real user info."""
    user = api_client.get_user_info()
    assert user.username is not None
    print(f"\n[Integration] Logged in as: {user.username}")
    print(f"[Integration] TLE hashes: {user.tle} (Type: {type(user.tle)})")
    if user.tle:
        print(f"[Integration] First TLE hash: {user.tle[0]} (Type: {type(user.tle[0])})")

def test_integration_get_stats(api_client):
    """Test retrieving real currency stats."""
    stats = api_client.get_currency_stats(TEST_SYMBOL)
    assert stats.bets >= 0
    print(f"[Integration] {TEST_SYMBOL} Main Balance: {stats.main_balance}")
    print(f"[Integration] {TEST_SYMBOL} Faucet Balance: {stats.faucet_balance}")

def test_integration_play_main_balance(api_client):
    """Test a small bet from main balance."""
    print(f"\n[Integration] Testing Main balance bet on {TEST_SYMBOL}...")
    try:
        resp = api_client.play_dice(
            symbol=TEST_SYMBOL,
            amount=MIN_AMOUNT,
            chance="50",
            is_high=True,
            faucet=False
        )
        assert resp.bet.hash is not None
        print(f"✓ Bet successful! Hash: {resp.bet.hash}, Result: {'Win' if resp.bet.result else 'Loss'}")
    except DuckDiceError as e:
        print(f"⚠ Bet failed: {e}")
        if "balance" not in str(e).lower() and "minimum bet" not in str(e).lower():
            raise

def test_integration_play_faucet_balance(api_client):
    """Test a small bet from faucet balance."""
    print(f"\n[Integration] Testing Faucet balance bet on {TEST_SYMBOL}...")
    try:
        resp = api_client.play_dice(
            symbol=TEST_SYMBOL,
            amount=MIN_AMOUNT,
            chance="50",
            is_high=True,
            faucet=True
        )
        assert resp.bet.hash is not None
        print(f"✓ Faucet bet successful! Hash: {resp.bet.hash}")
    except DuckDiceError as e:
        print(f"⚠ Faucet bet failed: {e}")
        if "balance" not in str(e).lower() and "minimum bet" not in str(e).lower():
            raise

def test_integration_play_tle_balance(api_client):
    """Test a small bet using a TLE hash if available."""
    user = api_client.get_user_info()
    if not user.tle:
        pytest.skip("No TLE hashes available for testing")
    
    tle_data = user.tle[0]
    # If tle_data is a dict (some APIs return objects), extract the hash
    tle_hash = tle_data.get("hash") if isinstance(tle_data, dict) else str(tle_data)
    
    print(f"\n[Integration] Testing TLE bet with hash {tle_hash}...")
    try:
        resp = api_client.play_dice(
            symbol=TEST_SYMBOL,
            amount=MIN_AMOUNT,
            chance="50",
            is_high=True,
            tle_hash=tle_hash
        )
        assert resp.bet.hash is not None
        print(f"✓ TLE bet successful! Hash: {resp.bet.hash}")
    except DuckDiceError as e:
        print(f"⚠ TLE bet failed: {e}")
        if "balance" not in str(e).lower() and "minimum bet" not in str(e).lower():
            raise

def test_integration_play_range_dice(api_client):
    """Test Range Dice integration."""
    print(f"\n[Integration] Testing Range Dice bet on {TEST_SYMBOL}...")
    try:
        resp = api_client.play_range_dice(
            symbol=TEST_SYMBOL,
            amount=MIN_AMOUNT,
            range_vals=[0, 4999],
            is_in=True
        )
        assert resp.bet.hash is not None
        print(f"✓ Range Dice bet successful! Hash: {resp.bet.hash}")
    except DuckDiceError as e:
        print(f"⚠ Range Dice bet failed: {e}")
        if "balance" not in str(e).lower() and "minimum bet" not in str(e).lower():
            raise
