"""
Game: Sudoku
------------
Sudoku 9x9 Solver

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Credit:
-------
- [Hardest sudoku](https://www.telegraph.co.uk/news/science/science-news/9359579/Worlds-hardest-sudoku-can-you-crack-it.html)
- [Solve algo](https://www.techwithtim.net/tutorials/python-programming/sudoku-solver-backtracking/)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Sudoku"]


# Library
# ---------------------------------------------------------------------------
from typing import Literal


# Class
# ---------------------------------------------------------------------------
class Sudoku:

    def __init__(self, sudoku_data: list[list[int]]) -> None:
        self.data = sudoku_data
        # self._original = sudoku_data # Make backup
        self._row_len = len(self.data)
        self._col_len = len(self.data[0])
        # self.solved = None

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.export_to_string()})"

    def __repr__(self) -> str:
        return self.__str__()

    def export_to_string(self, *, style: Literal["dot", "zero"] = "dot") -> str:
        """
        Export Sudoku data to string form

        Parameters
        ----------
        style : Literal["dot", "zero"]
            - "zero": ``0`` is ``0``
            - "dot": ``0`` is ``.``

        Returns
        -------
        str
            Sudoku string
        """
        style_option = ["zero", "dot"]
        if style.lower() not in style_option:
            style = "dot"

        out = "".join(str(self.data))
        remove = ["[", "]", " ", ","]
        for x in remove:
            out = out.replace(x, "")

        if style.startswith("zero"):
            return out
        elif style.startswith("dot"):
            out = out.replace("0", ".")
            return out
        else:
            return out

    @classmethod
    def from_string(cls, string_data: str):
        """
        Convert sudoku string format into `list`

        Parameters
        ----------
        string_data : str
            String data

        Returns
        -------
        Sudoku
            ``Sudoku`` instance


        Example:
        --------
        >>> Sudoku.from_string("8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..")
        [[8, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 3, 6, 0, 0, 0, 0, 0],
         [0, 7, 0, 0, 9, 0, 2, 0, 0],
         [0, 5, 0, 0, 0, 7, 0, 0, 0],
         [0, 0, 0, 0, 4, 5, 7, 0, 0],
         [0, 0, 0, 1, 0, 0, 0, 3, 0],
         [0, 0, 1, 0, 0, 0, 0, 6, 8],
         [0, 0, 8, 5, 0, 0, 0, 1, 0],
         [0, 9, 0, 0, 0, 0, 4, 0, 0]]
        """
        if len(string_data) == 81:
            # Convert
            sdk = str(string_data).replace(".", "0")

            # Divide into 9 equal parts
            temp = []
            while len(sdk) != 0:
                temp.append(sdk[:9])
                sdk = sdk[9:]

            # Turn into list[list[int]]
            out = []
            for value in temp:
                temp_list = [int(x) for x in value]
                out.append(temp_list)

        else:
            # Invalid length
            raise ValueError("Invalid length")
        return cls(out)

    @classmethod
    def hardest_sudoku(cls):
        """
        Create Hardest Sudoku instance
        ([Source](https://www.telegraph.co.uk/news/science/science-news/9359579/Worlds-hardest-sudoku-can-you-crack-it.html))

        Returns
        -------
        Sudoku
            ``Sudoku`` instance
        """
        return cls.from_string(
            "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
        )

    def to_board_form(self) -> str:
        """
        Prepare sudoku board ready to print

        Returns
        -------
        str
            Sudoku Board data that ready to print


        Example:
        --------
        >>> demo = Sudoku.hardest_sudoku()
        >>> print(demo.to_board_form())
        \u250E\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2512
        \u2503  8 0 0  \u2503  0 0 0  \u2503  0 0 0  \u2503
        \u2503  0 0 3  \u2503  6 0 0  \u2503  0 0 0  \u2503
        \u2503  0 7 0  \u2503  0 9 0  \u2503  2 0 0  \u2503
        \u2520\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2528
        \u2503  0 5 0  \u2503  0 0 7  \u2503  0 0 0  \u2503
        \u2503  0 0 0  \u2503  0 4 5  \u2503  7 0 0  \u2503
        \u2503  0 0 0  \u2503  1 0 0  \u2503  0 3 0  \u2503
        \u2520\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2528
        \u2503  0 0 1  \u2503  0 0 0  \u2503  0 6 8  \u2503
        \u2503  0 0 8  \u2503  5 0 0  \u2503  0 1 0  \u2503
        \u2503  0 9 0  \u2503  0 0 0  \u2503  4 0 0  \u2503
        \u2516\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u251A
        """
        out_string = ""
        for row in range(self._row_len):
            if row % 3 == 0:
                if row == 0:
                    out_string = out_string + " \u250E" + "\u2500" * 29 + "\u2512\n"
                else:
                    out_string = out_string + " \u2520" + "\u2500" * 29 + "\u2528\n"

            for col in range(self._col_len):
                if col % 3 == 0:
                    out_string += " \u2503  "

                if col == 8:
                    out_string = out_string + str(self.data[row][col]) + "  \u2503\n"
                else:
                    out_string = out_string + str(self.data[row][col]) + " "

        out_string = out_string + " \u2516" + "\u2500" * 29 + "\u251A"
        return out_string

    # Solve
    def _find_empty(self):
        """
        Find the empty cell (value = 0)

        Return postion(row, col)

        If not empty then return `None`
        """
        for row in range(self._row_len):
            for col in range(self._col_len):
                if self.data[row][col] == 0:
                    # Return position when empty
                    return (row, col)
        # Return None when there is no empty cell
        return None

    def _is_valid(self, number: int, position: tuple[int, int]) -> bool:
        """
        Check valid number value in row, column, box
        """
        row, col = position  # unpack tuple

        # Check row
        for i in range(self._col_len):  # each item in row i; row i has `col_len` items
            if self.data[row][i] == number and col != i:
                return False

        # Check column
        for i in range(self._row_len):
            if self.data[i][col] == number and row != i:
                return False

        # Check box
        box_x = col // 3
        box_y = row // 3

        for i in range(box_y * 3, box_y * 3 + 3):
            for j in range(box_x * 3, box_x * 3 + 3):
                if self.data[i][j] == number and (i, j) != position:
                    return False

        # If everything works
        return True

    def _solve(self) -> bool:
        """
        Solve sudoku (backtracking method)
        """
        # Find empty cell
        empty_pos = self._find_empty()
        if empty_pos is None:
            return True  # solve_state (True: every cell filled)
        else:
            # unpack position when exist empty cell
            row, col = empty_pos

        for num in range(1, 10):  # sudoku value (1-9)
            if self._is_valid(num, empty_pos):
                self.data[row][col] = num

                # Recursive
                if self._solve():
                    return True

                self.data[row][col] = 0

        # End recursive
        return False

    def solve(self):
        """
        Solve the Sudoku

        Returns
        -------
        Sudoku
            ``Sudoku`` instance


        Example:
        --------
        >>> test = Sudoku.hardest_sudoku()
        >>> test.solve()
        >>> print(test.to_board_form())
         \u250E\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2512
         \u2503  8 1 2  \u2503  7 5 3  \u2503  6 4 9  \u2503
         \u2503  9 4 3  \u2503  6 8 2  \u2503  1 7 5  \u2503
         \u2503  6 7 5  \u2503  4 9 1  \u2503  2 8 3  \u2503
         \u2520\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2528
         \u2503  1 5 4  \u2503  2 3 7  \u2503  8 9 6  \u2503
         \u2503  3 6 9  \u2503  8 4 5  \u2503  7 2 1  \u2503
         \u2503  2 8 7  \u2503  1 6 9  \u2503  5 3 4  \u2503
         \u2520\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2528
         \u2503  5 2 1  \u2503  9 7 4  \u2503  3 6 8  \u2503
         \u2503  4 3 8  \u2503  5 2 6  \u2503  9 1 7  \u2503
         \u2503  7 9 6  \u2503  3 1 8  \u2503  4 5 2  \u2503
         \u2516\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u251A
        """
        self._solve()
        # self.solved = self.data
        # self.data = self._original
        return self.__class__(self.data)


# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test = Sudoku.hardest_sudoku()
    print(test.solve().to_board_form())
