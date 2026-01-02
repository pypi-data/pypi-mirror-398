"""
Test: Util
----------
Text table

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import os

import pytest

from absfuyu.util.text_table import BoxDrawingCharacterNormal, OneColumnTableMaker


@pytest.fixture
def table_maker():
    return OneColumnTableMaker(ncols=None, style="normal")


@pytest.mark.abs_util
class TestOneColumnTableMaker:
    """absfuyu.util.text_table.OneColumnTableMaker"""

    def test_init_default_ncols(self, table_maker: OneColumnTableMaker) -> None:
        assert table_maker.ncols >= 5

    def test_init_custom_ncols(self) -> None:
        maker = OneColumnTableMaker(ncols=10)
        assert maker.ncols == 10

    def test_init_min_ncols(self) -> None:
        maker = OneColumnTableMaker(ncols=3)
        assert maker.ncols == 5

    def test_add_title_short(self, table_maker: OneColumnTableMaker) -> None:
        table_maker.add_title("Short Title")
        assert len(table_maker._title) == table_maker.ncols

    def test_add_title_long(self, table_maker: OneColumnTableMaker) -> None:
        mul = table_maker.ncols + 5
        table_maker.add_title("A" * mul)
        assert len(table_maker._title) == table_maker.ncols

    def test_add_paragraph_single_string(
        self, table_maker: OneColumnTableMaker
    ) -> None:
        table_maker.add_paragraph("Hello")
        assert table_maker._paragraphs == [["Hello"]]

    def test_add_paragraph_multiple_strings(
        self, table_maker: OneColumnTableMaker
    ) -> None:
        table_maker.add_paragraph(["Hello", "World"])
        assert table_maker._paragraphs == [["Hello", "World"]]

    def test_make_line_upper(self, table_maker: OneColumnTableMaker) -> None:
        line = table_maker._make_line(0)
        assert line.startswith(BoxDrawingCharacterNormal.UPPER_LEFT_CORNER)
        assert line.endswith(BoxDrawingCharacterNormal.UPPER_RIGHT_CORNER)

    def test_make_line_intersect(self, table_maker: OneColumnTableMaker) -> None:
        line = table_maker._make_line(1)
        assert line.startswith(BoxDrawingCharacterNormal.VERTICAL_RIGHT)
        assert line.endswith(BoxDrawingCharacterNormal.VERTICAL_LEFT)

    def test_make_line_lower(self, table_maker: OneColumnTableMaker) -> None:
        line = table_maker._make_line(2)
        assert line.startswith(BoxDrawingCharacterNormal.LOWER_LEFT_CORNER)
        assert line.endswith(BoxDrawingCharacterNormal.LOWER_RIGHT_CORNER)

    def test_make_table_empty(self, table_maker: OneColumnTableMaker) -> None:
        assert table_maker._make_table() is None

    def test_make_table_single_paragraph(
        self, table_maker: OneColumnTableMaker
    ) -> None:
        table_maker.add_paragraph(["Hello", "World"])
        table = table_maker._make_table()
        assert table is not None
        assert len(table) > 0

    def test_make_table_multiple_paragraphs(
        self, table_maker: OneColumnTableMaker
    ) -> None:
        table_maker.add_paragraph(["Hello", "World"])
        table_maker.add_paragraph(["Foo", "Bar"])
        table = table_maker._make_table()
        assert table is not None
        assert len(table) > 0

    def test_make_table_with_title(self, table_maker: OneColumnTableMaker) -> None:
        table_maker.add_title("My Title")
        table_maker.add_paragraph(["Hello", "World"])
        table = table_maker._make_table()
        assert table is not None
        assert len(table) > 0

    def test_make_table_output(self, table_maker: OneColumnTableMaker) -> None:
        table_maker.add_paragraph(["Hello", "World"])
        output = table_maker.make_table()
        assert isinstance(output, str)
        assert len(output) > 0

    @pytest.mark.parametrize("terminal_size", [80, 120])
    def test_init_terminal_size_mock(self, mocker, terminal_size: int) -> None:
        mock_get_size = mocker.patch("os.get_terminal_size")
        # mock_get_size.side_effect = OSError("")
        mock_get_size.return_value.columns = terminal_size
        # with pytest.raises(OSError):
        #     assert maker.ncols == 88
        maker = OneColumnTableMaker()
        assert maker.ncols == terminal_size
