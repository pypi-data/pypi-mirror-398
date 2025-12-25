"""DuckDice API Client"""
from dataclasses import dataclass
import requests

class DuckDiceAPIException(Exception):
    """Base exception for DuckDice API errors"""
    pass

@dataclass
class DuckDiceConfig:
    """Configuration for DuckDice API client"""
    api_key: str
    base_url: str = "https://duckdice.io/api"
    timeout: int = 30

class DuckDiceAPI:
    """DuckDice API Client"""
    def __init__(self, config: DuckDiceConfig):
        self.config = config
        self.session = requests.Session()
