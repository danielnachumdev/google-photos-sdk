from typing import Optional
from .....utils import Printable, Dictable


class Date(Printable, Dictable):
    """A wrapper class over Date object
    Args:
        year (int): 
        month (int): 
        day (int): 
    """

    def __init__(self, year: int, month: int, day: int) -> None:
        self.year = year
        self.month = month
        self.day = day

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class DateRange(Printable, Dictable):
    """A wrapper class to specify a range of dates to use as a filter
    Args:
        startDate (Date): the start date of the range
        endDate (Date): the end date of the range
    """

    def __init__(self, startDate: Date, endDate: Date) -> None:
        self.startDate = startDate
        self.endDate = endDate

    def to_dict(self) -> dict:
        return {
            "startDate": self.startDate.to_dict(),
            "endDate": self.endDate.to_dict()
        }


class DateFilter(Printable, Dictable):
    """
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems/search#datefilter
    This filter defines the allowed dates or date ranges for the media returned.
    It's possible to pick a set of specific dates and a set of date ranges.
    Media items uploaded without metadata specifying the date the media item was
    captured will not be returned in queries using date filters.
    Google Photos server upload time is not used as a fallback in this case.

    Args:
        dates (Optional[list[Date]], optional): List of dates that match the media items' creation date. 
            A maximum of 5 dates can be included per request. Defaults to None.
        ranges (Optional[list[DateRange]], optional): List of dates ranges that match the media items' creation date. 
            A maximum of 5 dates ranges can be included per request. Defaults to None.
    """

    def __init__(self, dates: Optional[list[Date]] = None, ranges: Optional[list[DateRange]] = None) -> None:
        if not dates and not ranges:
            raise ValueError(
                "When creating a DateFilter, must supply at-least one of 'dates', 'ranges'")

        if dates:
            if not (0 < len(dates) <= 5):  # pylint: disable=unneeded-not,superfluous-parens
                raise ValueError(
                    "A maximum of 5 dates can be included per request.")
        if ranges:
            if not (0 < len(ranges) <= 5):  # pylint: disable=unneeded-not,superfluous-parens
                raise ValueError(
                    "A maximum of 5 dates ranges can be included per request.")
        self.dates = dates
        self.ranges = ranges

    def to_dict(self) -> dict:
        res: dict = {}
        if self.dates:
            res["dates"] = [
                d.__dict__ for d in self.dates
            ]
        if self.ranges:
            res["ranges"] = [
                r.to_dict() for r in self.ranges
            ]
        return res


__all__ = [
    "Date",
    "DateRange",
    "DateFilter"
]
