from enum import Enum
from .....utils import Printable, Dictable


class MediaType(Enum):
    """An Enum to specify the available Media types to use as a filter"""
    ALL_MEDIA = "ALL_MEDIA"
    VIDEO = "VIDEO"
    PHOTO = "PHOTO"


class MediaTypeFilter(Printable, Dictable):
    """
    see https://developers.google.com/photos/library/reference/rest/v1/mediaItems/search#mediatypefilter
    """

    def __init__(self, mediaTypes: list[MediaType]) -> None:
        if len(mediaTypes) != 1:
            raise ValueError(
                "This field should be populated with only one media type. "
                "If you specify multiple media types, it results in an error.")
        self.mediaTypes = mediaTypes

    def to_dict(self) -> dict:
        return {
            "mediaTypes": [e.value for e in self.mediaTypes]
        }
