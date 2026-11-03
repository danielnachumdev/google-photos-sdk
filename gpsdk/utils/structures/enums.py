from enum import Enum


class RequestType(Enum):
    """An inner use Enum to specify which types of request can be sent with the API
    """
    GET = "get"
    POST = "post"
    PATCH = "patch"


class HeaderType(Enum):
    """An inner use Enum to specify which types of headers should be sent with requests
    """
    DEFAULT = ""
    JSON = "json"
    OCTET = "octet-stream"


class MimeType(Enum):
    """An enum to specify the supported mime-types"""
    PNG = "image/png"
    JPEG = "image/jpeg"
    MP4 = "video/mp4"
    MOV = "video/quicktime"
    WMV = "x-ms-asf"


class PositionType(Enum):
    """enum to be used with GooglePhotosAlbum.add_enrichment to specify
    the relative location of the enrichment in the album
    """
    POSITION_TYPE_UNSPECIFIED = "POSITION_TYPE_UNSPECIFIED"
    FIRST_IN_ALBUM = "FIRST_IN_ALBUM"
    LAST_IN_ALBUM = "LAST_IN_ALBUM"
    AFTER_MEDIA_ITEM = "AFTER_MEDIA_ITEM"
    AFTER_ENRICHMENT_ITEM = "AFTER_ENRICHMENT_ITEM"


class EnrichmentType(Enum):
    """enum to be used with GooglePhotosAlbum.add_enrichment to specify the type of enrichment
    """
    TEXT_ENRICHMENT = "textEnrichment"
    LOCATION_ENRICHMENT = "locationEnrichment"
    MAP_ENRICHMENT = "mapEnrichment"


class MediaItemMaskTypes(Enum):
    """
    available mask values to update for a media item
    see https://developers.google.com/photos/library/reference/rest/v1/mediaItems/patch#query-parameters
    """
    DESCRIPTION = "description"


class AlbumMaskType(Enum):
    """Enum to specify which fields are applicable regarding updatable fields in albums"""
    TITLE = "title"
    COVER_PHOTOS_MEDIA_ITEM_ID = "coverPhotoMediaItemId"


class RelativeItemType(Enum):
    """Enum to specify which type of relativity the PositionType refers to if applicable
    """
    relativeMediaItemId = "relativeMediaItemId"
    relativeEnrichmentItemId = "relativeEnrichmentItemId"


class StatusCode(Enum):
    """
    see https://developers.google.com/photos/library/reference/rest/v1/Status
    and https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto
    """
    OK = 0
    CANCELLED = 1
    UNKNOWN = 2
    INVALID_ARGUMENT = 3
    DEADLINE_EXCEEDED = 4
    NOT_FOUND = 5
    ALREADY_EXISTS = 6
    PERMISSION_DENIED = 7
    UNAUTHENTICATED = 16
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    UNIMPLEMENTED = 12
    INTERNAL = 13
    UNAVAILABLE = 14
    DATA_LOSS = 15
