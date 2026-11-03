from typing import Optional
from enum import Enum
from .....utils import Printable, Dictable


class ContentCategory(Enum):
    """
    https://developers.google.com/photos/library/reference/rest/v1/mediaItems/search#contentcategory
    """
    NONE = "NONE"
    LANDSCAPES = "LANDSCAPES"
    RECEIPTS = "RECEIPTS"
    CITYSCAPES = "CITYSCAPES"
    LANDMARKS = "LANDMARKS"
    SELFIES = "SELFIES"
    PEOPLE = "PEOPLE"
    PETS = "PETS"
    WEDDINGS = "WEDDINGS"
    BIRTHDAYS = "BIRTHDAYS"
    DOCUMENTS = "DOCUMENTS"
    TRAVEL = "TRAVEL"
    ANIMALS = "ANIMALS"
    FOOD = "FOOD"
    SPORT = "SPORT"
    NIGHT = "NIGHT"
    PERFORMANCES = "PERFORMANCES"
    WHITEBOARDS = "WHITEBOARDS"
    SCREENSHOTS = "SCREENSHOTS"
    UTILITY = "UTILITY"
    ARTS = "ARTS"
    CRAFTS = "CRAFTS"
    FASHION = "FASHION"
    HOUSES = "HOUSES"
    GARDENS = "GARDENS"
    FLOWERS = "FLOWERS"
    HOLIDAYS = "HOLIDAYS"


class ContentFilter(Printable, Dictable):
    """
    see https://developers.google.com/photos/library/reference/rest/v1/mediaItems/search#contentfilter

    This filter allows you to return media items based on the content type.
    It's possible to specify a list of categories to include, and/or a list of categories to exclude.
    Within each list, the categories are combined with an OR.
    The content filter includedContentCategories: [c1, c2, c3] would get media items that contain (c1 OR c2 OR c3).
    The content filter excludedContentCategories: [c1, c2, c3] would NOT get media items that contain (c1 OR c2 OR c3).
    You can also include some categories while excluding others, as in this example: 
        includedContentCategories: [c1, c2], excludedContentCategories: [c3, c4]
    The previous example would get media items that contain (c1 OR c2) AND NOT (c3 OR c4).
    A category that appears in includedContentCategories must not appear in excludedContentCategories.

    Args:
        includedContentCategories (Optional[list[ContentCategory]], optional): 
            The set of categories to be included in the media item search results.
            The items in the set are ORed. There's a maximum of 10 includedContentCategories per request. 
            Defaults to None.
        excludedContentCategories (Optional[list[ContentCategory]], optional): 
            The set of categories which are not to be included in the media item search results.
            The items in the set are ORed. There's a maximum of 10 excludedContentCategories per request.
            Defaults to None.

    Raises:
        ValueError: if not values are supplied
        ValueError: if 'includedContentCategories' has more than 10 values
        ValueError: if 'excludedContentCategories' has more than 10 values
    """

    def __init__(
        self,
        includedContentCategories: Optional[list[ContentCategory]] = None,
        excludedContentCategories: Optional[list[ContentCategory]] = None
    ) -> None:
        if not includedContentCategories and not excludedContentCategories:
            raise ValueError(
                "When creating a ContentFilter, one must supply at-least one from "
                "'includedContentCategories', 'excludedContentCategories'")

        if includedContentCategories:
            if not (0 < len(includedContentCategories) < 10):  # pylint: disable=unneeded-not,superfluous-parens
                raise ValueError(
                    "There's a maximum of 10 includedContentCategories per request.")

        if excludedContentCategories:
            if not (0 < len(excludedContentCategories) < 10):  # pylint: disable=unneeded-not,superfluous-parens
                raise ValueError(
                    "There's a maximum of 10 excludedContentCategories per request.")
        self.includedContentCategories = includedContentCategories
        self.excludedContentCategories = excludedContentCategories

    def to_dict(self) -> dict:
        res: dict = {}
        if self.includedContentCategories:
            res["includedContentCategories"] = [
                e.value for e in self.includedContentCategories]
        if self.excludedContentCategories:
            res["excludedContentCategories"] = [
                e.value for e in self.excludedContentCategories]
        return res
