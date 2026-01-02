"""
Absfuyu: Tarot
--------------
Tarot stuff


Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Usage:
------
>>> tarot_deck = Tarot()
>>> print(tarot_deck.random_card())
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Tarot", "TarotCard"]


# Library
# ---------------------------------------------------------------------------
import random

from absfuyu.core import BaseClass, versionadded
from absfuyu.logger import logger
from absfuyu.pkg_data import DataList, DataLoader


# Class
# ---------------------------------------------------------------------------
@versionadded("2.6.0")
class TarotCard:
    """Tarot card"""

    def __init__(
        self,
        name: str,
        rank: int,
        suit: str,
        meanings: dict[str, list[str]],
        keywords: list[str],
        fortune_telling: list[str],
    ) -> None:
        self.name = name.title()
        self.rank = rank
        self.suit = suit
        self.meanings = meanings
        self.keywords = keywords
        self.fortune_telling = fortune_telling

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self) -> str:
        return self.__str__()


@versionadded("2.6.0")
class Tarot(BaseClass):
    """Tarot data"""

    def __init__(self) -> None:
        self.data_location = DataList.TAROT

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"

    @property
    def tarot_deck(self) -> list[TarotCard]:
        """
        Load pickled tarot data

        :rtype: list[TarotCard]
        """
        tarot_data: list = DataLoader(self.data_location).load()
        logger.debug(f"{len(tarot_data)} tarot cards loaded")
        return [
            TarotCard(
                name=x["name"],
                rank=x["rank"],
                suit=x["suit"],
                meanings=x["meanings"],
                keywords=x["keywords"],
                fortune_telling=x["fortune_telling"],
            )
            for x in tarot_data
        ]

    def random_card(self) -> TarotCard:
        """
        Pick a random tarot card

        Returns
        -------
        TarotCard
            Random Tarot card
        """
        return random.choice(self.tarot_deck)
