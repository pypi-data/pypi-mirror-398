"""
Test: Passwordlib

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

from itertools import combinations_with_replacement

import pytest

from absfuyu.dxt import Text
from absfuyu.tools.passwordlib import TOTP, PasswordGenerator

# def test_generate_password():
#     test = [password_check(Password.generate_password()) for _ in range(100)]
#     assert all(test)


class TestPasswordlib:
    def test_generate_password_matrix(self) -> None:
        num_of_test = 1000

        def check(value: dict) -> int:
            return sum([1 for x in value.values() if x > 0])

        out = []
        check_matrix = list(
            set(
                combinations_with_replacement(
                    [True, False, True, False, True, False], 3
                )
            )
        )
        for x in check_matrix:
            include_number, include_special, include_uppercase = x
            check_value = sum(x) + 1

            test = [
                Text(
                    PasswordGenerator.generate_password(
                        include_number=include_number,
                        include_special=include_special,
                        include_uppercase=include_uppercase,
                    )
                ).analyze()
                for _ in range(num_of_test)
            ]
            test = list(set(map(check, test)))
            if len(test) == 1:
                out.append(test[0] == check_value)
            else:
                # assert False
                raise AssertionError()

        assert all(out)

    def test_generate_passphrase(self) -> None:
        _ = PasswordGenerator.generate_passphrase(
            num_of_blocks=3,
            block_divider="-",
            first_letter_cap=True,
            include_number=True,
        )


class TestTOTP:
    def test_totp_initialization(self):
        totp = TOTP(secret="BASE32SECRET")
        assert totp.secret == "BASE32SECRET"
        assert totp.name == "None"
        assert totp.issuer is None
        assert totp.algorithm == "SHA1"
        assert totp.digit == 6
        assert totp.period == 30

    def test_totp_initialization_with_optional_parameters(self):
        totp = TOTP(
            secret="ANOTHERSECRET",
            name="TestUser",
            issuer="TestIssuer",
            algorithm="SHA256",
            digit=8,
            period=60,
        )
        assert totp.secret == "ANOTHERSECRET"
        assert totp.name == "TestUser"
        assert totp.issuer == "TestIssuer"
        assert totp.algorithm == "SHA256"
        assert totp.digit == 8
        assert totp.period == 60

    def test_totp_secret_is_uppercase(self):
        totp = TOTP(secret="lowercase")
        assert totp.secret == "LOWERCASE"

    def test_totp_digit_and_period_are_at_least_one(self):
        totp = TOTP(secret="SECRET", digit=0, period=0)
        assert totp.digit == 1
        assert totp.period == 1

    def test_to_url_with_all_parameters(self):
        totp = TOTP(
            secret="FULLSECRET",
            name="Full User",
            issuer="FullIssuer",
            algorithm="SHA512",
            digit=8,
            period=120,
        )
        url = totp.to_url()
        expected_url = (
            "otpauth://totp/Full%20User?"
            "secret=FULLSECRET&"
            "issuer=FullIssuer&"
            "algorithm=SHA512&"
            "digit=8&"
            "period=120"
        )
        assert url == expected_url
