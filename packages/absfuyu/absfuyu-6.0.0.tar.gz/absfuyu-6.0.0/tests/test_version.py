"""
Test: Version

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from itertools import product

import pytest

from absfuyu.version import Bumper, ReleaseLevel, ReleaseOption, Version


# Version
class TestVersion:
    @pytest.mark.parametrize(
        ["major", "minor", "patch", "serial"], [(1, 0, 0, 5), ("1", "0", "0", "8")]
    )
    def test_init(
        self,
        major: int | str,
        minor: int | str,
        patch: int | str,
        serial: int | str,
    ) -> None:
        try:
            _ = Version(major, minor, patch, ReleaseLevel.DEV, serial)
            assert True
        except Exception as err:
            # assert False
            raise AssertionError(err)

    @pytest.mark.parametrize("data", [list(), dict(), set(), tuple()])
    def test_init_error(self, data) -> None:
        with pytest.raises(TypeError) as excinfo:
            _ = Version(data, data, data)
        assert str(excinfo.value)

    @pytest.mark.parametrize("tuple_", [(1, 0, 0), (1, 0, 0, "dev", 0)])
    def test_from_tuple(self, tuple_: tuple) -> None:
        try:
            _ = Version.from_tuple(tuple_)
            assert True
        except Exception as err:
            # assert False
            raise AssertionError(err)

    def test_from_tuple_error(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            _ = Version.from_tuple((1, 0))
        assert str(excinfo.value)

    @pytest.mark.parametrize(
        "str_", ["1.0.0 ", " 100.8.48", "1.5.2.dev2", "1.2.4.rc8456", "1.9.4.final2"]
    )
    def test_from_str(self, str_: str) -> None:
        try:
            _ = Version.from_str(str_)
            assert True
        except Exception as err:
            # assert False
            raise AssertionError(err)

    @pytest.mark.parametrize("str_", ["1.0.0s", "5555.1.fnl5"])
    def test_from_str_error(self, str_: str) -> None:
        with pytest.raises(ValueError) as excinfo:
            _ = Version.from_str(str_)
        assert str(excinfo.value)


# Bumper
def list_of_bumper_bump_test() -> list[
    tuple[tuple[int, int, int, str, int], str, str, str]
]:
    bumper_list: list[tuple[int, int, int, str, int]] = [
        (1, 0, 0, ReleaseLevel.FINAL, 0),
        (1, 3, 2, ReleaseLevel.FINAL, 0),
        (2, 4, 6, ReleaseLevel.RC, 0),
        (2, 4, 6, ReleaseLevel.DEV, 0),
    ]
    release_options: list[str] = [
        ReleaseOption.MAJOR,
        ReleaseOption.MINOR,
        ReleaseOption.PATCH,
    ]
    release_levels: list[str] = [ReleaseLevel.FINAL, ReleaseLevel.DEV, ReleaseLevel.RC]
    merged = list(product(bumper_list, release_options, release_levels))
    # TODO: Improve this
    result_list: list[str] = [
        # 1.0.0
        "2.0.0",  # major final
        "2.0.0.dev0",  # major dev
        "2.0.0.rc0",  # major rc
        "1.1.0",  # minor final
        "1.1.0.dev0",  # minor dev
        "1.1.0.rc0",  # minor rc
        "1.0.1",  # patch final
        "1.0.1.dev0",  # patch dev
        "1.0.1.rc0",  # patch rc
        # 1.3.2
        "2.0.0",  # major
        "2.0.0.dev0",
        "2.0.0.rc0",
        "1.4.0",  # minor
        "1.4.0.dev0",
        "1.4.0.rc0",
        "1.3.3",  # patch
        "1.3.3.dev0",
        "1.3.3.rc0",
        # 2.4.6.rc0
        "2.4.6",  # major
        "3.0.0.dev0",
        "2.4.6.rc1",
        "2.4.6",  # minor
        "2.5.0.dev0",
        "2.4.6.rc1",
        "2.4.6",  # patch
        "2.4.7.dev0",
        "2.4.6.rc1",
        # 2.4.6.dev0
        "2.4.6",  # major
        "2.4.6.dev1",
        "2.4.6.rc0",
        "2.4.6",  # minor
        "2.4.6.dev1",
        "2.4.6.rc0",
        "2.4.6",  # patch
        "2.4.6.dev1",
        "2.4.6.rc0",
    ]
    if not len(result_list) == len(merged):
        # Check length
        raise ValueError("length of result_list is not in correct length")
    out: list[tuple[Bumper, str, str, str]] = [
        (x[0], x[1], x[2], result_list[i]) for i, x in enumerate(merged)
    ]
    return out


class TestBumper:
    @pytest.mark.parametrize(
        "bumper, release_option, release_channel, desired_output",
        list_of_bumper_bump_test(),
    )
    def test_bump(
        self,
        bumper: tuple[int, int, int, str, int],
        release_option: str,
        release_channel: str,
        desired_output: str,
    ) -> None:
        bumper: Bumper = Bumper.from_tuple(bumper)
        bumper.bump(option=release_option, channel=release_channel)
        assert str(bumper) == desired_output
