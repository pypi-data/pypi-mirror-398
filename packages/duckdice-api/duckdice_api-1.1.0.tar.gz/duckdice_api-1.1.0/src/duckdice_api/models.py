from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BalanceInfo:
    currency: str
    main: str = "0"
    faucet: str = "0"
    bonus: str = "0"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BalanceInfo":
        return cls(
            currency=data.get("currency", ""),
            main=str(data.get("main", data.get("amount", "0"))),
            faucet=str(data.get("faucet", "0")),
            bonus=str(data.get("bonus", "0")),
        )


@dataclass
class WageringBonus:
    name: str
    type: str
    hash: str
    status: str
    symbol: str
    margin: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WageringBonus":
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            hash=data.get("hash", ""),
            status=data.get("status", ""),
            symbol=data.get("symbol", ""),
            margin=str(data.get("margin", "0")),
        )


@dataclass
class UserInfo:
    hash: str
    username: str
    created_at: int
    level: int
    balances: List[BalanceInfo] = field(default_factory=list)
    wagering_bonuses: List[WageringBonus] = field(default_factory=list)
    tle: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserInfo":
        return cls(
            hash=data.get("hash", ""),
            username=data.get("username", ""),
            created_at=data.get("createdAt", 0),
            level=data.get("level", 0),
            balances=[BalanceInfo.from_dict(b) for b in data.get("balances", [])],
            wagering_bonuses=[WageringBonus.from_dict(b) for b in data.get("wageringBonuses", [])],
            tle=data.get("tle", []),
        )


@dataclass
class CurrencyStats:
    bets: int
    wins: int
    profit: str
    volume: str
    main_balance: str
    faucet_balance: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurrencyStats":
        balances = data.get("balances", {})
        return cls(
            bets=int(data.get("bets", 0)),
            wins=int(data.get("wins", 0)),
            profit=str(data.get("profit", "0")),
            volume=str(data.get("volume", "0")),
            main_balance=str(balances.get("main", "0")),
            faucet_balance=str(balances.get("faucet", "0")),
        )


@dataclass
class Bet:
    hash: str
    symbol: str
    result: bool
    choice: str
    choice_option: Optional[str]
    number: int
    chance: float
    payout: float
    bet_amount: str
    win_amount: str
    profit: str
    nonce: int
    created: int
    game_mode: str
    game_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bet":
        return cls(
            hash=data.get("hash", ""),
            symbol=data.get("symbol", ""),
            result=bool(data.get("result")),
            choice=data.get("choice", ""),
            choice_option=data.get("choiceOption"),
            number=int(data.get("number", 0)),
            chance=float(data.get("chance", 0)),
            payout=float(data.get("payout", 0)),
            bet_amount=str(data.get("betAmount", "0")),
            win_amount=str(data.get("winAmount", "0")),
            profit=str(data.get("profit", "0")),
            nonce=int(data.get("nonce", 0)),
            created=int(data.get("created", 0)),
            game_mode=data.get("gameMode", ""),
            game_metadata=data.get("game", {}),
        )


@dataclass
class PlayResponse:
    bet: Bet
    user: Optional[UserInfo]
    is_jackpot: bool = False
    jackpot_status: Optional[bool] = None
    jackpot_amount: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayResponse":
        return cls(
            bet=Bet.from_dict(data.get("bet", {})),
            user=UserInfo.from_dict(data.get("user", {})) if "user" in data else None,
            is_jackpot=bool(data.get("isJackpot")),
            jackpot_status=data.get("jackpotStatus"),
            jackpot_amount=data.get("jackpot", {}).get("amount") if isinstance(data.get("jackpot"), dict) else None,
        )
