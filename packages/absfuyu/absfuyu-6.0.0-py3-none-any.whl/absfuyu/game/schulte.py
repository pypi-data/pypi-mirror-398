"""
Game: Schulte
-------------

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["SchulteTable"]


# Library
# ---------------------------------------------------------------------------
from absfuyu.core.baseclass import BaseClass
from absfuyu.dxt import ListExt
from absfuyu.util.text_table import BoxStyle, get_box_drawing_character


# Function
# ---------------------------------------------------------------------------
def draw_grid(data: list[list[int]], style: BoxStyle = "normal"):
    chars = get_box_drawing_character(style=style)
    rows = len(data)
    cols = len(data[0])

    # find max width for padding
    cell_width = max(len(str(x)) for row in data for x in row) + 2

    def horizontal_border(left: str, middle: str, right: str) -> str:
        return left + (chars.HORIZONTAL * cell_width + middle) * (cols - 1) + chars.HORIZONTAL * cell_width + right

    # top border
    print(horizontal_border(chars.UPPER_LEFT_CORNER, chars.HORIZONTAL_DOWN, chars.UPPER_RIGHT_CORNER))

    for i, row in enumerate(data):
        # content line
        line = chars.VERTICAL + "".join(f"{str(val):^{cell_width}}" + chars.VERTICAL for val in row)
        print(line)

        # middle or bottom border
        if i < rows - 1:
            print(horizontal_border(chars.VERTICAL_RIGHT, chars.CROSS, chars.VERTICAL_LEFT))
        else:
            print(horizontal_border(chars.LOWER_LEFT_CORNER, chars.HORIZONTAL_UP, chars.LOWER_RIGHT_CORNER))


# Class
# ---------------------------------------------------------------------------
class SchulteTable(BaseClass):
    """
    A Schulte Table is a cognitive training tool consisting of a grid filled
    with randomly placed numbers. The task is to find and select all the numbers
    in ascending order as quickly as possible. This exercise helps improve
    visual attention, focus, processing speed, mental flexibility,
    and peripheral vision.
    """

    def __init__(self, size: int = 5) -> None:
        self.size = max(size, 1)

    def make_table(self) -> None:
        data = ListExt(range(1, self.size**2 + 1)).shuffle().split_chunk(self.size)
        draw_grid(data)

    # def play(self):
    #     """GUI"""
    #     from absfuyu.util.gui import CustomTkinterApp

    #     class Schulte(CustomTkinterApp):
    #         def __init__(self, title: str | None = None, size: tuple[int, int] | None = None) -> None:
    #             super().__init__(title=title, size=size)


if __name__ == "__main__":
    t = SchulteTable(5)
    print(t)
