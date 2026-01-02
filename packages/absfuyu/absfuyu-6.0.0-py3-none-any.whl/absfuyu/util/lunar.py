# flake8: noqa
"""
Absfuyu: Lunar calendar
-----------------------
Convert to lunar calendar

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)

Source:
-------
Astronomical algorithms from the book "Astronomical Algorithms" by Jean Meeus, 1998
https://www.informatik.uni-leipzig.de/~duc/amlich/AL.py
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["LunarCalendar"]


# Library
# ---------------------------------------------------------------------------
import math
from datetime import date, datetime


# Class
# ---------------------------------------------------------------------------
class LunarCalendar:
    """Lunar Calendar"""

    def __init__(
        self,
        year: int,
        month: int,
        day: int,
        *,
        time_zone: int = 7,
        lunar_leap: bool = False,
    ) -> None:
        """
        :param time_zone: Time zone
        :param lunar_leap: Do not use this
        """
        self.date = date(year, month, day)
        self.time_zone = time_zone
        self._lunar_leap = lunar_leap

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.date}|lunar_leap={self._lunar_leap})"

    def __repr__(self) -> str:
        return self.__str__()

    def _julian_day_from_date(
        self,
        *,
        overwrite_year: int | None = None,
        overwrite_month: int | None = None,
        overwrite_day: int | None = None,
    ) -> int:
        """
        Compute the (integral) Julian day number of `self.date`

        i.e., the number of days between 1/1/4713 BC (Julian calendar) and `self.date`.
        """
        day = self.date.day if overwrite_day is None else overwrite_day
        month = self.date.month if overwrite_month is None else overwrite_month
        year = self.date.year if overwrite_year is None else overwrite_year
        a = int((14 - month) / 12.0)
        y = year + 4800 - a
        m = month + 12 * a - 3
        jd = (
            day
            + int((153 * m + 2) / 5.0)
            + 365 * y
            + int(y / 4.0)
            - int(y / 100.0)
            + int(y / 400.0)
            - 32045
        )
        if jd < 2299161:
            jd = day + int((153 * m + 2) / 5.0) + 365 * y + int(y / 4.0) - 32083
        return jd

    @staticmethod
    def _julian_day_to_date(julian_day: int) -> date:
        """
        Convert a Julian day number to `datetime.date`

        julian_day: Julian day
        """
        if julian_day > 2299160:
            ## After 5/10/1582, Gregorian calendar
            a = julian_day + 32044
            b = int((4 * a + 3) / 146097.0)
            c = a - int((b * 146097) / 4.0)
        else:
            b = 0
            c = julian_day + 32082

        d = int((4 * c + 3) / 1461.0)
        e = c - int((1461 * d) / 4.0)
        m = int((5 * e + 2) / 153.0)
        day = e - int((153 * m + 2) / 5.0) + 1
        month = m + 3 - 12 * int(m / 10.0)
        year = b * 100 + d - 4800 + int(m / 10.0)
        return date(year, month, day)

    @staticmethod
    def _new_moon(k: int) -> float:
        """
        Compute the time of the k-th new moon after the new moon of `1/1/1900 13:52 UCT`
        measured as the number of days since `1/1/4713 BC noon UCT`,
        e.g., `2451545.125 is 1/1/2000 15:00 UTC`.

        Example:
        `2415079.9758617813` for `k=2` or `2414961.935157746` for `k=-2`
        """
        ## Time in Julian centuries from 1900 January 0.5
        T = k / 1236.85
        T2 = math.pow(T, 2)
        T3 = math.pow(T, 3)
        dr = math.pi / 180.0
        Jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
        Jd1 = Jd1 + 0.00033 * math.sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
        ## Mean new moon
        M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
        ## Sun's mean anomaly
        Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
        ## Moon's mean anomaly
        F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
        ## Moon's argument of latitude
        C1 = (0.1734 - 0.000393 * T) * math.sin(M * dr) + 0.0021 * math.sin(2 * dr * M)
        C1 = C1 - 0.4068 * math.sin(Mpr * dr) + 0.0161 * math.sin(dr * 2 * Mpr)
        C1 = C1 - 0.0004 * math.sin(dr * 3 * Mpr)
        C1 = C1 + 0.0104 * math.sin(dr * 2 * F) - 0.0051 * math.sin(dr * (M + Mpr))
        C1 = (
            C1 - 0.0074 * math.sin(dr * (M - Mpr)) + 0.0004 * math.sin(dr * (2 * F + M))
        )
        C1 = (
            C1
            - 0.0004 * math.sin(dr * (2 * F - M))
            - 0.0006 * math.sin(dr * (2 * F + Mpr))
        )
        C1 = (
            C1
            + 0.0010 * math.sin(dr * (2 * F - Mpr))
            + 0.0005 * math.sin(dr * (2 * Mpr + M))
        )
        if T < -11:
            deltat = (
                0.001
                + 0.000839 * T
                + 0.0002261 * T2
                - 0.00000845 * T3
                - 0.000000081 * T * T3
            )
        else:
            deltat = -0.000278 + 0.000265 * T + 0.000262 * T2
        JdNew = Jd1 + C1 - deltat
        return JdNew

    @staticmethod
    def _sun_longitude(julian_day_noon: float) -> float:
        """
        Compute the longitude of the sun at any time.

        julian_day_noon: The number of days since `1/1/4713 BC noon`.
        """
        T = (julian_day_noon - 2451545.0) / 36525.0
        # Time in Julian centuries
        # from 2000-01-01 12:00:00 GMT
        T2 = math.pow(T, 2)
        T3 = math.pow(T, 3)
        dr = math.pi / 180.0  # degree to radian
        M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T3
        # mean anomaly, degree
        L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
        # mean longitude, degree
        DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * math.sin(dr * M)
        DL += (0.019993 - 0.000101 * T) * math.sin(dr * 2 * M) + 0.000290 * math.sin(
            dr * 3 * M
        )
        L = L0 + DL  # true longitude, degree
        L = L * dr
        L = L - math.pi * 2 * (int(L / (math.pi * 2)))
        # Normalize to (0, 2*math.pi)
        return L

    def _get_sun_longitude(self, day_number: int) -> int:
        """
        Compute sun position at midnight of the day with the given Julian day number.

        The time zone if the time difference between local time and UTC: 7.0 for UTC+7:00.

        The function returns a number between `0` and `11`.

        From the day after March equinox and the 1st major term after March equinox, 0 is returned. After that, return 1, 2, 3 ...
        """
        return int(
            self._sun_longitude(day_number - 0.5 - self.time_zone / 24.0) / math.pi * 6
        )

    def _get_new_moon_day(self, k: int) -> int:
        """
        Compute the day of the k-th new moon in the given time zone.

        The time zone if the time difference between local time and UTC: 7.0 for UTC+7:00.
        """
        return int(self._new_moon(k) + 0.5 + self.time_zone / 24.0)

    def _get_lunar_month_11(self, *, overwrite_year: int | None = None) -> int:
        """
        Find the day that starts the luner month 11
        of the given year for the given time zone.
        """
        # off = self._julian_day_from_date(overwrite_month=12, overwrite_day=31) - 2415021.076998695
        year = self.date.year if overwrite_year is None else overwrite_year
        off = (
            self._julian_day_from_date(
                overwrite_month=12, overwrite_day=31, overwrite_year=year
            )
            - 2415021.0
        )
        k = int(off / 29.530588853)
        nm = self._get_new_moon_day(k)
        sunLong = self._get_sun_longitude(nm)
        #### sun longitude at local midnight
        if sunLong >= 9:
            nm = self._get_new_moon_day(k - 1)
        return nm

    def _get_leap_month_offset(self, a11: int) -> int:
        """
        Find the index of the leap month after the month starting on the day a11.
        """
        k = int((a11 - 2415021.076998695) / 29.530588853 + 0.5)
        last = 0
        i = 1  # start with month following lunar month 11
        arc = self._get_sun_longitude(self._get_new_moon_day(k + i))
        while True:
            last = arc
            i += 1
            arc = self._get_sun_longitude(self._get_new_moon_day(k + i))
            if not (arc != last and i < 14):
                break

        # for i in range(1, 14):
        #     arc = self._get_sun_longitude(self._get_new_moon_day(k + i))
        #     if arc != last:
        #         last = arc
        #     else:
        #         break
        return i - 1

    def to_lunar(self):
        """
        Convert solar date to the corresponding lunar date.

        Returns
        -------
        LunarCalendar
            LunarCalendar instance
        """
        yy = self.date.year
        day_number = self._julian_day_from_date()
        k = int((day_number - 2415021.076998695) / 29.530588853)
        month_start = self._get_new_moon_day(k + 1)
        if month_start > day_number:
            month_start = self._get_new_moon_day(k)
        # alert(day_number + " -> " + month_start)
        a11 = self._get_lunar_month_11()
        b11 = a11
        if a11 >= month_start:
            lunar_year = yy
            a11 = self._get_lunar_month_11(overwrite_year=yy - 1)
        else:
            lunar_year = yy + 1
            b11 = self._get_lunar_month_11(overwrite_year=yy + 1)
        lunar_day = day_number - month_start + 1
        diff = int((month_start - a11) / 29.0)
        lunar_month = diff + 11
        if b11 - a11 > 365:
            leap_month_diff = self._get_leap_month_offset(a11)
            if diff >= leap_month_diff:
                lunar_month = diff + 10
                if diff == leap_month_diff:
                    self._lunar_leap = True
        if lunar_month > 12:
            lunar_month = lunar_month - 12
        if lunar_month >= 11 and diff < 4:
            lunar_year -= 1
        return self.__class__(
            lunar_year, lunar_month, lunar_day, lunar_leap=self._lunar_leap
        )

    def to_solar(self):
        """
        Convert a lunar date to the corresponding solar date.

        Returns
        -------
        LunarCalendar
            LunarCalendar instance

        date
            When unable to convert
        """
        lunarD = self.date.day
        lunarM = self.date.month
        lunarY = self.date.year
        if lunarM < 11:
            a11 = self._get_lunar_month_11(overwrite_year=lunarY - 1)
            b11 = self._get_lunar_month_11(overwrite_year=lunarY)
        else:
            a11 = self._get_lunar_month_11(overwrite_year=lunarY)
            b11 = self._get_lunar_month_11(overwrite_year=lunarY + 1)
        k = int(0.5 + (a11 - 2415021.076998695) / 29.530588853)
        off = lunarM - 11
        if off < 0:
            off += 12
        if b11 - a11 > 365:
            leapOff = self._get_leap_month_offset(a11)
            leapM = leapOff - 2
            if leapM < 0:
                leapM += 12
            if self._lunar_leap is True and lunarM != leapM:
                # logger.warning("lunar_leap is True")
                # raise ValueError()
                return date(1, 1, 1)
            elif self._lunar_leap is True or off >= leapOff:
                off += 1
        monthStart = self._get_new_moon_day(k + off)
        out = self._julian_day_to_date(monthStart + lunarD - 1)
        return self.__class__(out.year, out.month, out.day, lunar_leap=self._lunar_leap)

    def convert_all(self) -> dict:
        """
        Convert to both lunar and solar

        This method has no practical use

        :rtype: dict
        """
        return {"lunar": self.to_lunar(), "original": self, "solar": self.to_solar()}

    @classmethod
    def from_solar(cls, year: int, month: int, day: int, lunar_leap: bool = False):
        """
        Convert to lunar day from solar day

        Parameters
        ----------
        year : int
            Year (in range [1, 9999])

        month : int
            Month (in range [1, 12])

        day : int
            Day (in range [1, 31])

        lunar_leap : bool
            Is leap (Default: ``False``)

        Returns
        -------
        LunarCalendar
            LunarCalendar instance
        """
        return cls(year, month, day, lunar_leap=lunar_leap).to_lunar()

    @classmethod
    def from_datetime(cls, datetime_object: date | datetime):
        """
        Convert from ``datetime.datetime`` object

        Parameters
        ----------
        datetime_object : date | datetime
            ``datetime.datetime`` object

        Returns
        -------
        LunarCalendar
            LunarCalendar instance
        """
        return cls(datetime_object.year, datetime_object.month, datetime_object.day)

    @classmethod
    def now(cls):
        """
        Get lunar calendar for ``datetime.datetime.now()``

        Returns
        -------
        LunarCalendar
            LunarCalendar instance
        """
        today = datetime.now().date()
        return cls(today.year, today.month, today.day).to_lunar()
