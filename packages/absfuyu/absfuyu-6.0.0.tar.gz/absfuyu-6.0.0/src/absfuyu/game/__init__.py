"""
Absfuyu: Game
-------------
Contain some game that can be played on terminal

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "game_escapeLoop",
    "game_RockPaperScissors",
]


# Library
# ---------------------------------------------------------------------------
import random
import time

from .game_stat import GameStats

# Game
# ---------------------------------------------------------------------------
# Escape loop
_ESCAPE_LOOP_GAME_MSG = """\
Are you sure about this?
Don't leave me =((
I can't believe you did this to me!
Are you very much sure?
I'll be sad. Pick again please.
I still don't believe you.
Choose again.
You actually have to answer the correct keyword
I think you need to choose again.
Last chance!
Okay okay, i believe you ;)
Almost there.
I can do this all day
So close!
You can't escape from me.
How are you still here, just to suffer?
Never gonna give you up
Never gonna let you down
"""


def game_escapeLoop() -> None:
    """Try to escape the infinite loop"""

    init = True
    welcome_messages = [
        "Congrats! You are now stuck inside an infinite loop.",
        "Do you want to escape this loop?",
    ]

    num1 = random.choice(range(2, 13))
    num2 = random.choice(range(2, 13))
    hidden_answer = str(num1 * num2)

    gm_msg = {x for x in _ESCAPE_LOOP_GAME_MSG.splitlines() if len(x) > 0}
    game_messages = list(gm_msg) + [
        f"Hint 01: The keyword is: {num1}",
        f"Hint 02: {num2}",
    ]

    congrats_messages = ["Congratulation! You've escaped."]

    start_time = time.time()
    while True:
        # Welcome
        if init:
            for x in welcome_messages:
                print(x)
            answer = str(input())
            init = False

        # Random text
        mess = random.choice(game_messages)
        print(mess)

        # Condition check
        answer = str(input())
        if answer == hidden_answer:
            for x in congrats_messages:
                print(x)
            stop_time = time.time()
            break
    print(f"= Escaped in {stop_time - start_time:,.2f}s =")


# Rock Paper Scissors
def game_RockPaperScissors(hard_mode: bool = False) -> GameStats:
    """
    Rock Paper Scissors

    :param hard_mode: The bot only win or draw (Default: ``False``)
    :type hard_mode: bool
    """

    state_dict = {"0": "rock", "1": "paper", "2": "scissors"}

    init = True

    end_message = "end"

    welcome_messages = [
        "Welcome to Rock Paper Scissors",
        f"Type '{end_message}' to end",
    ]

    game_messages = [
        "Pick one option to begin:",
        " ".join([f"{k}={v}" for k, v in state_dict.items()]),
    ]

    game_summary = GameStats()

    while True:
        # Welcome
        if init:
            for x in welcome_messages:
                print(x)
            init = False

        # Game start
        print("")
        for x in game_messages:
            print(x)

        # Player's choice
        answer = input().strip().lower()

        # Condition check
        if answer == end_message:
            print(game_summary)
            break

        elif answer not in ["0", "1", "2"]:
            print("Invalid option. Choose again!")

        else:
            # Calculation
            if hard_mode:
                if answer == "0":
                    game_choice = random.choice(["0", "1"])
                if answer == "1":
                    game_choice = random.choice(["1", "2"])
                if answer == "2":
                    game_choice = random.choice(["0", "2"])
            else:
                game_choice = random.choice(["0", "1", "2"])
            print(f"You picked: {state_dict[answer]}")
            print(f"BOT picked: {state_dict[game_choice]}")

            if answer == "2" and game_choice == "0":
                print("You Lose!")
                game_summary.update_score("lose")
            elif answer == "0" and game_choice == "2":
                print("You Win!")
                game_summary.update_score("win")
            elif answer == game_choice:
                print("Draw Match!")
                game_summary.update_score("draw")
            elif answer > game_choice:
                print("You Win!")
                game_summary.update_score("win")
            else:
                print("You Lose!")
                game_summary.update_score("lose")

    return game_summary
