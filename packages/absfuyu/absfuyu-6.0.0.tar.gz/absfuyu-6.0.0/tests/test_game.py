"""
Test: Game

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from typing import Literal

import pytest

from absfuyu.game.game_stat import GameStats


class TestGameStat:
    @pytest.mark.parametrize("score_option", ["win", "draw", "lose"])
    def test_update_score(self, score_option: Literal["win", "draw", "lose"]) -> None:
        instance = GameStats()
        before = getattr(instance, score_option)
        instance.update_score(score_option)
        after = getattr(instance, score_option)
        assert after - before == 1

    @pytest.mark.parametrize("score_option", ["w", "d", "l"])
    def test_update_score_error(
        self, score_option: Literal["win", "draw", "lose"]
    ) -> None:
        instance = GameStats()
        with pytest.raises(AttributeError) as excinfo:
            instance.update_score(score_option)
        assert str(excinfo.value)
