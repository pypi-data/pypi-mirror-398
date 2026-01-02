"""
Game: Tic Tac Toe
-----------------

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["TicTacToe", "GameMode"]


# Library
# ---------------------------------------------------------------------------
import random
import time
from typing import Literal, NamedTuple

from absfuyu.core import BaseClass, CLITextColor, versionadded

# Type
# ---------------------------------------------------------------------------
BoardGame = list[list[str]]


# Class
# ---------------------------------------------------------------------------
class Pos(NamedTuple):
    """Position"""

    row: int
    col: int


class GameMode:
    ONE_V_ONE = "1v1"
    ONE_V_BOT = "1v0"
    BOT_V_BOT = "0v0"


class GameStateResult(NamedTuple):
    key: str
    location: Literal["col", "row", "diag", "blank"]
    pos: int


@versionadded("3.3.3")
class TicTacToe(BaseClass):
    """Tic Tac Toe game"""

    def __init__(
        self,
        game_size: int = 3,
        *,
        x: str = "X",
        o: str = "O",
        blank: str = " ",
        position_split_symbol: str = ",",
        end_break_word: str = "END",
        welcome_message: bool = True,
    ) -> None:
        """
        :param game_size: Board size (Default: 3x3)
        :param x: X symbol
        :param o: O symbol
        :param blank: Blank symbol
        :param position_split_symbol: Position split symbol
        :param end_break_word: End break word
        :param welcome_message: Show welcome message (Default: `True`)
        """

        # Board size
        self.row_size = game_size
        self.col_size = game_size

        # Game setting
        self.X = x
        self.O = o  # noqa: E741
        self.BLANK = blank
        self.POS_SPLIT = position_split_symbol
        self.END_BREAK = end_break_word
        self.welcome_message = welcome_message

        # Init board
        self.board = self._gen_board()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(game_size={self.row_size})"

    # Game
    def _gen_board(self) -> BoardGame:
        """
        Generate board game
        """
        board = [
            [self.BLANK for _ in range(self.row_size)] for _ in range(self.col_size)
        ]
        return board

    def _check_state(self) -> GameStateResult:
        """
        Check game winning state

        Returns
        -------
        dict[str, str | int]
            ``X`` | ``O`` | ``BLANK``
        """

        # Check rows
        for row in range(self.row_size):
            if len(set(self.board[row])) == 1:
                key = list(set(self.board[row]))[0]
                return GameStateResult(key, "row", row)
                # return {"key": key, "location": "row", "pos": row}  # modified

        # Check cols
        for col in range(self.col_size):
            temp = [self.board[row][col] for row in range(self.row_size)]
            if len(set(temp)) == 1:
                key = list(set(temp))[0]
                return GameStateResult(key, "col", col)
                # return {"key": key, "location": "col", "pos": col}  # modified

        # Check diagonal
        diag1 = [self.board[i][i] for i in range(len(self.board))]
        if len(set(diag1)) == 1:
            key = list(set(diag1))[0]
            return GameStateResult(key, "diag", 1)
            # return {"key": key, "location": "diag", "pos": 1}  # modified

        diag2 = [self.board[i][len(self.board) - i - 1] for i in range(len(self.board))]
        if len(set(diag2)) == 1:
            key = list(set(diag2))[0]
            return GameStateResult(key, "diag", 2)
            # return {"key": key, "location": "diag", "pos": 2}  # modified

        # Else
        return GameStateResult(self.BLANK, "blank", 0)
        # return {"key": self.BLANK}

    @staticmethod
    def _print_board(board: BoardGame) -> None:
        """
        Print Tic Tac Toe board
        """
        nrow, ncol = len(board), len(board[0])
        length = len(board)
        print(f"{'+---'*length}+")
        for row in range(nrow):
            for col in range(ncol):
                print(f"| {board[row][col]} ", end="")
            print(f"|\n{'+---'*length}+")

    def _win_hightlight(self) -> BoardGame:
        """
        Hight light the win by removing other placed key
        """

        # Get detailed information
        detail = self._check_state()
        loc = detail.location
        loc_line = detail.pos

        # Make new board
        board = self._gen_board()

        # Fill in the hightlighted content
        if loc.startswith("col"):
            for i in range(len(board)):
                board[i][loc_line] = detail.key
        elif loc.startswith("row"):
            for i in range(len(board)):
                board[loc_line][i] = detail.key
        else:
            if loc_line == 1:
                for i in range(len(board)):
                    board[i][i] = detail.key
            else:
                for i in range(len(board)):
                    board[i][len(board) - i - 1] = detail.key

        # Output
        return board

    def _is_blank(self, pos: Pos) -> bool:
        """Check if current pos is filled"""
        return self.board[pos.row][pos.col] == self.BLANK

    @staticmethod
    def _convert_bot_output(pos: Pos) -> Pos:
        """
        Turn to real pos by:

        - +1 to ``row`` and ``col``
        - convert into ``str``
        """
        return Pos(pos.row + 1, pos.col + 1)

    def _generate_random_move(self) -> Pos:
        """
        Generate a random move from board game
        """
        while True:
            output = Pos(
                random.randint(0, len(self.board) - 1),
                random.randint(0, len(self.board) - 1),
            )
            if self._is_blank(output):
                break
        return self._convert_bot_output(output)

    def play(
        self,
        game_mode: str = GameMode.ONE_V_BOT,
        *,
        bot_time: float = 0,
    ) -> None:
        """
        Play a game of Tic Tac Toe

        Parameters
        ----------
        game_mode : str
            Game mode

        bot_time : float
            Time sleep between each bot move (Default: ``0``)
        """
        # Init game
        filled = 0
        current_player = self.X
        state = self._check_state().key
        BOT = False
        BOT2 = False

        # Welcome message
        if self.welcome_message:
            print(
                f"""\
{CLITextColor.GREEN}Welcome to Tic Tac Toe!

{CLITextColor.YELLOW}Rules: Match lines vertically, horizontally or diagonally
{CLITextColor.YELLOW}{self.X} goes first, then {self.O}
{CLITextColor.RED}Type '{self.END_BREAK}' to end the game{CLITextColor.RESET}"""
            )

        # Check gamemode
        _game_mode = [
            "1v1",  # Player vs player
            "1v0",  # Player vs BOT
            "0v0",  # BOT vs BOT
        ]
        if game_mode not in _game_mode:
            game_mode = _game_mode[1]  # Force vs BOT
        if game_mode.startswith(GameMode.ONE_V_BOT):
            BOT = True
        if game_mode.startswith(GameMode.BOT_V_BOT):
            BOT = True
            BOT2 = True

        # Game
        self._print_board(self.board)

        place_pos = None
        while state == self.BLANK and filled < self.row_size**2:
            print(f"{CLITextColor.BLUE}{current_player}'s turn:{CLITextColor.RESET}")

            try:  # Error handling
                if (BOT and current_player == self.O) or BOT2:
                    move = self._generate_random_move()
                    str_move = f"{move.row}{self.POS_SPLIT}{move.col}"
                    move = str_move  # type: ignore
                else:
                    move = input(  # type: ignore
                        f"Place {CLITextColor.BLUE}{current_player}{CLITextColor.RESET} at {CLITextColor.BLUE}<row{self.POS_SPLIT}col>:{CLITextColor.RESET} "
                    )

                if move.upper() == self.END_BREAK:  # type: ignore # Failsafe
                    print(f"{CLITextColor.RED}Game ended{CLITextColor.RESET}")
                    break

                move = move.split(self.POS_SPLIT)  # type: ignore
                row = int(move[0])
                col = int(move[1])
                place_pos = Pos(row - 1, col - 1)

                if self._is_blank(place_pos):
                    self.board[place_pos.row][place_pos.col] = current_player
                    filled += 1

                else:  # User and BOT error
                    print(
                        f"{CLITextColor.RED}Invalid move, please try again{CLITextColor.RESET}"
                    )
                    continue

            except Exception:  # User error
                print(
                    f"{CLITextColor.RED}Invalid move, please try again{CLITextColor.RESET}"
                )
                continue

            state = self._check_state().key
            self._print_board(self.board)

            if state != self.BLANK:
                print(f"{CLITextColor.GREEN}{state} WON!{CLITextColor.RESET}")
                self._print_board(self._win_hightlight())

            # Change turn
            if BOT2:  # BOT delay
                time.sleep(bot_time)

            if current_player == self.X:
                current_player = self.O
            else:
                current_player = self.X

        if state == self.BLANK and filled == self.row_size**2:
            print(f"{CLITextColor.YELLOW}Draw Match!{CLITextColor.RESET}")
