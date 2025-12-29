"""Enums for UFaaS application."""

from enum import StrEnum


class Currency(StrEnum):
    # none = "none"

    IRR = "IRR"
    # IRT = "IRT"

    USD = "USD"
    EUR = "EUR"
    # GBP = "GBP"

    # USDT = "USDT"
    # BTC = "BTC"
    # ETH = "ETH"

    @classmethod
    def main_currency(cls) -> "Currency":
        return cls.IRR

    @property
    def properties(self) -> dict[str, dict[str, str | int | bool]]:
        return {
            Currency.IRR: {
                "name": {
                    "fa": "ریال",
                    "en": "Iranian Rial",
                },
                "symbol": "IRR",
                "precision": 0,
                "icon": "https://flagcdn.com/w40/ir.png",
                "is_crypto": False,
                "color": "#1976d2",
            },
            Currency.USD: {
                "name": {
                    "fa": "دلار",
                    "en": "Dollar",
                },
                "symbol": "USD",
                "precision": 2,
                "icon": "https://flagcdn.com/w40/us.png",
                "is_crypto": False,
                "color": "#f7931a",
            },
            Currency.EUR: {
                "name": {
                    "fa": "یورو",
                    "en": "Euro",
                },
                "symbol": "EUR",
                "precision": 2,
                "icon": "https://flagcdn.com/w40/eu.png",
                "is_crypto": False,
                "color": "#26a17b",
            },
        }

    @property
    def currency(self) -> "Currency":
        return self

    @property
    def name(self) -> dict:
        return self.properties.get(self, {}).get("name")

    @property
    def symbol(self) -> str:
        return self.properties.get(self, {}).get("symbol")

    @property
    def precision(self) -> int:
        return self.properties.get(self, {}).get("precision")

    @property
    def icon(self) -> str:
        return self.properties.get(self, {}).get("icon")

    @property
    def is_crypto(self) -> bool:
        return self.properties.get(self, {}).get("is_crypto")

    @property
    def color(self) -> str:
        return self.properties.get(self, {}).get("color")


class StatusEnum(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
