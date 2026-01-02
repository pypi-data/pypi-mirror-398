"""
Absfuyu: Human
--------------
Human related stuff

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["Human", "Person"]


# Library
# ---------------------------------------------------------------------------
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import Self

from absfuyu.core import BaseClass
from absfuyu.dxt import IntExt
from absfuyu.fun import zodiac_sign

# from dateutil.relativedelta import relativedelta


# Class
# ---------------------------------------------------------------------------
class BloodType(StrEnum):
    A_PLUS = "A+"
    A_MINUS = "A-"
    AB_PLUS = "AB+"
    AB_MINUS = "AB-"
    B_PLUS = "B+"
    B_MINUS = "B-"
    O_PLUS = "O+"
    O_MINUS = "O-"
    A = "A"
    AB = "AB"
    B = "B"
    O = "O"
    OTHER = "OTHER"


class Human(BaseClass):
    """
    Basic human data
    """

    def __init__(
        self,
        first_name: str,
        last_name: str | None = None,
        birthday: str | datetime | None = None,
        birth_time: str | None = None,
        gender: bool | None = None,
        height: int | float | None = None,
        weight: int | float | None = None,
        blood_type: BloodType = BloodType.OTHER,
    ) -> None:
        """
        Human instance

        Parameters
        ----------
        first_name : str
            First name

        last_name : str | None, optional
            Last name, by default ``None``

        birthday : str | datetime | None, optional
            Birthday in format: ``yyyy/mm/dd``, by default ``None`` (birthday = today)

        birth_time : str | None, optional
            Birth time in format: ``hh:mm``, by default ``None`` (birthtime = today)

        gender : bool | None, optional
            ``True``: Male; ``False``: Female (biologicaly), by default ``None``

        height : int | float | None, optional
            Height in centimeter (cm), by default ``None``

        weight : int | float | None, optional
            Weight in kilogram (kg), by default ``None``

        blood_type : BloodType, optional
            Blood type, by default ``BloodType.OTHER``
        """

        # Name
        self.first_name = first_name
        self.last_name = last_name
        self.name = (
            f"{self.last_name}, {self.first_name}"
            if self.last_name is not None
            else self.first_name
        )

        # Birthday
        now = datetime.now()
        if birthday is None:
            modified_birthday = now.date()
        elif isinstance(birthday, str):
            for x in ["/", "-"]:
                birthday = birthday.replace(x, "/")
            modified_birthday = datetime.strptime(birthday, "%Y/%m/%d")
        else:
            modified_birthday = birthday

        if birth_time is None:
            modified_birthtime = now.time()
        else:
            birth_time = list(map(int, birth_time.split(":")))  # type: ignore
            modified_birthtime = time(*birth_time)

        self.birthday = date(
            modified_birthday.year, modified_birthday.month, modified_birthday.day
        )
        self.birth_time = modified_birthtime

        self.birth = datetime(
            modified_birthday.year,
            modified_birthday.month,
            modified_birthday.day,
            modified_birthtime.hour,
            modified_birthtime.minute,
        )

        # Others
        self.gender = gender
        self.height = height
        self.weight = weight
        self.blood_type = blood_type

    def __str__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({str(self.name)})"

    @classmethod
    def JohnDoe(cls) -> Self:
        """
        Dummy Human for test

        Returns
        -------
        Human
            Dummy Human instance
        """
        return cls("John", "Doe", "1980/01/01", "00:00", True, 180, 80, BloodType.O)

    @property
    def is_male(self) -> bool:
        """
        Check if male (biological)

        Returns
        -------
        bool
            - ``True``: Male
            - ``False``: Female
        """
        if self.gender is None:
            raise ValueError("Gender must be defined first")
        return self.gender

    @property
    def age(self) -> float:
        """
        Calculate age based on birthday, precise to birth_time

        Returns
        -------
        float
            Age
        """
        now = datetime.now()
        # age = now - self.birthday
        rdelta = now - self.birth
        # rdelta = relativedelta(now, self.birthday)
        # return round(rdelta.years + rdelta.months / 12, 2)
        return round(rdelta / timedelta(days=365.2425), 2)

    @property
    def is_adult(self) -> bool:
        """
        Check if ``self.age`` >= ``18``

        Returns
        -------
        bool
            If is adult
        """
        return self.age >= 18

    @property
    def bmi(self) -> float:
        r"""
        Body Mass Index (kg/m^2)

        Formula: :math:`\frac{weight (kg)}{height (m)^2}`

        - BMI < 18.5: Skinny
        - 18.5 < BMI < 25: Normal
        - BMI > 30: Obesse

        Returns
        -------
        float
            BMI value
        """
        if self.height is None or self.weight is None:
            raise ValueError("Height and Weight must be defined")

        height_in_meter = self.height / 100
        bmi = self.weight / (height_in_meter**2)
        return round(bmi, 2)

    def update(self, data: dict) -> None:
        """
        Update Human data

        Parameters
        ----------
        data : dict
            Data

        Returns
        -------
        None
        """
        self.__dict__.update(data)


class Person(Human):
    """
    More detailed ``Human`` data
    """

    def __init__(
        self,
        first_name,
        last_name=None,
        birthday=None,
        birth_time=None,
        gender=None,
        height=None,
        weight=None,
        blood_type=BloodType.OTHER,
    ) -> None:
        super().__init__(
            first_name,
            last_name,
            birthday,
            birth_time,
            gender,
            height,
            weight,
            blood_type,
        )
        self.address: str = None  # type: ignore
        self.hometown: str = None  # type: ignore
        self.email: str = None  # type: ignore
        self.phone_number: str = None  # type: ignore
        self.nationality: str = None  # type: ignore
        self.likes: list = None  # type: ignore
        self.hates: list = None  # type: ignore
        self.education: str = None  # type: ignore
        self.occupation: str = None  # type: ignore
        self.personality: str = None  # type: ignore
        self.note: str = None  # type: ignore

    @property
    def zodiac_sign(self) -> str:
        """
        Zodiac sign of ``Person``

        Returns
        -------
        str
            Zodiac sign
        """
        return zodiac_sign(self.birthday.day, self.birthday.month)

    @property
    def zodiac_sign_13(self) -> str:
        """
        Zodiac sign of ``Person`` (13 zodiac signs version)

        Returns
        -------
        str
            Zodiac sign
        """
        return zodiac_sign(self.birthday.day, self.birthday.month, zodiac13=True)

    @property
    def numerology(self) -> int:
        """
        Numerology number of ``Person``

        Returns
        -------
        int
            Numerology number
        """
        temp = f"{self.birthday.year}{self.birthday.month}{self.birthday.day}"
        return IntExt(temp).add_to_one_digit(master_number=True)
