"""
Game: Game Stat

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["GameStats"]


# Library
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field
from typing import Literal


# Class
# ---------------------------------------------------------------------------
@dataclass
class GameStats:
    win: int = field(default=0)
    draw: int = field(default=0)
    lose: int = field(default=0)
    win_rate: str = field(init=False)
    _win_rate: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._update_win_rate()

    def _update_win_rate(self) -> None:
        try:
            self._win_rate = self.win / (self.win + self.draw + self.lose)
            self.win_rate = f"{self._win_rate * 100:,.2f}%"
        except ZeroDivisionError:
            self._win_rate = 0
            self.win_rate = "N/A"

    def update_score(self, option: Literal["win", "draw", "lose"]) -> None:
        self.__setattr__(option, self.__getattribute__(option) + 1)
        self._update_win_rate()
