"""
ABSFUYU CLI
-----------
Game

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["game_group"]


# Library
# ---------------------------------------------------------------------------
import click

from absfuyu.game import game_escapeLoop, game_RockPaperScissors
from absfuyu.game.schulte import SchulteTable
from absfuyu.game.sudoku import Sudoku
from absfuyu.game.tictactoe import GameMode, TicTacToe
from absfuyu.game.wordle import Wordle


# CLI
# ---------------------------------------------------------------------------
@click.command
@click.option(
    "--hard",
    "hard_mode",
    is_flag=True,
    default=False,
    show_default=True,
    help="Hard mode",
)
def rps(hard_mode: bool) -> None:
    """Game: Rock Paper Scissors"""
    game_RockPaperScissors(hard_mode=hard_mode)


@click.command(name="esl")
def escape_loop() -> None:
    """Game: Escape loop"""
    game_escapeLoop()


@click.command(name="wordle")
def wordle_solver() -> None:
    """Worldle solver"""
    Wordle().solve()


@click.command(name="sudoku")
@click.argument("sudoku_string", type=str)
@click.option(
    "--raw",
    "raw",
    is_flag=True,
    default=False,
    show_default=True,
    help="Returns answer in string form",
)
def sudoku_solver(sudoku_string: str, raw: bool) -> None:
    """Sudoku solver"""
    sdk = Sudoku.from_string(sudoku_string)
    if raw:
        click.echo(sdk.solve().export_to_string())
    else:
        click.echo(sdk.solve().to_board_form())


@click.command(name="ttt")
@click.option(
    "--size",
    "-s",
    "size",
    type=int,
    default=3,
    show_default=True,
    help="Size of the board",
)
@click.option(
    "--mode",
    "-m",
    "game_mode",
    type=click.Choice([GameMode.ONE_V_BOT, GameMode.ONE_V_ONE, GameMode.BOT_V_BOT]),
    default=GameMode.ONE_V_BOT,
    show_default=True,
    help="Game mode",
)
@click.option(
    "--bot-time",
    "-t",
    "bot_time",
    type=float,
    default=0.0,
    show_default=True,
    help="Time between bot move",
)
def tictactoe(size: int, game_mode: str, bot_time: float) -> None:
    """Game: Tictactoe"""
    instance = TicTacToe(size)
    instance.play(game_mode, bot_time=bot_time)


@click.command(name="schulte")
@click.option(
    "--size",
    "-s",
    "size",
    type=int,
    default=5,
    show_default=True,
    help="Size of the table",
)
def schulte_table(size: int) -> None:
    """Schulte table"""
    engine = SchulteTable(size=size)
    engine.make_table()


@click.group(name="game")
def game_group() -> None:
    """Play game"""
    pass


game_group.add_command(rps)
game_group.add_command(escape_loop)
game_group.add_command(wordle_solver)
game_group.add_command(sudoku_solver)
game_group.add_command(tictactoe)
game_group.add_command(schulte_table)
