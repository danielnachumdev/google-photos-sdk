from datetime import datetime
from typing import Optional
import gpsdk
from .parent_classes import Printable, Dictable
from .enums import PositionType, StatusCode
Milliseconds = float
Seconds = float
MediaItemID = str
UploadToken = str
Url = str
AlbumId = str
Path = str
NextPageToken = str
Value = str


class SimpleMediaItem(Dictable, Printable):
    """A simple media item to be created in Google Photos via an upload token.

    Args:
        uploadToken (str): Token identifying the media bytes that have been uploaded to Google.
        fileName (Optional[str]): File name with extension of the media item. 
            This is shown to the user in Google Photos. 
            The file name specified during the byte upload process is ignored if this field is set. 
            The file name, including the file extension, shouldn't be more than 255 characters. 
            This is an optional field.

    Raises:
        ValueError: fileName's length must be less than 256 characters long
    """
    # see https://developers.google.com/photos/library/reference/rest/v1/mediaItems/batchCreate#SimpleMediaItem

    @staticmethod
    def from_dict(dct: dict):
        return SimpleMediaItem(
            uploadToken=dct["uploadToken"],
            fileName=dct["fileName"] if "fileName" in dct else None
        )

    def __init__(self, uploadToken: str, fileName: Optional[str] = None) -> None:
        if fileName:
            if len(fileName) > 255:
                raise ValueError(
                    "'fileName' must not be more than 255 characters or the request will fail")
        self.__uploadToken = uploadToken
        self.__fileName = fileName

    @property
    def fileName(self):
        """File name with extension of the media item. 
        This is shown to the user in Google Photos. 
        The file name specified during the byte upload process is ignored if this field is set. 
        The file name, including the file extension, shouldn't be more than 255 characters. 
        This is an optional field.
        """
        return self.__fileName

    @property
    def uploadToken(self):
        """Token identifying the media bytes that have been uploaded to Google.
        """
        return self.__uploadToken


class NewMediaItem(Dictable, Printable):
    """New media item that's created in a user's Google Photos account.

    Args:
        description (str): Description of the media item. 
        This is shown to the user in the item's info section in the Google Photos app. 
        Must be shorter than 1000 characters. Only include text written by users. 
        Descriptions should add context and help users understand media. 
        Do not include any auto-generated strings such as filenames, tags, and other metadata.
        simpleMediaItem (SimpleMediaItem): A new media item that has been uploaded via the included uploadToken.

    Raises:
        ValueError: if description is more than 1000 characters long

    """
    @staticmethod
    def from_dict(dct: dict):
        return NewMediaItem(
            description=dct["description"],
            simpleMediaItem=SimpleMediaItem.from_dict(dct["simpleMediaItem"])
        )

    def __init__(self, description: str, simpleMediaItem: SimpleMediaItem) -> None:
        if description:
            if len(description) > 1000:
                raise ValueError(
                    "\"description\"'s length should be shorter than 1000 characters long")
        self.__description = description
        self.__simpleMediaItem = simpleMediaItem

    @property
    def description(self):
        """returns the NewMediaItem's description
        """
        return self.__description

    @property
    def simpleMediaItem(self):
        """returns the NewMediaItem's SimpleMediaItem
        """
        return self.__simpleMediaItem


class AlbumPosition(Dictable, Printable):
    """Specifies a position in an album.

        Args:
            position (PositionType, optional): Type of position, for a media or enrichment item. 
                Defaults to PositionType.FIRST_IN_ALBUM.
            relativeMediaItemId (Optional[str], optional): The media item to which the position is relative to. 
                Only used when position type is AFTER_MEDIA_ITEM. Defaults to None.
            relativeEnrichmentItemId (Optional[str], optional): 
                The enrichment item to which the position is relative to. 
                Only used when position type is AFTER_ENRICHMENT_ITEM. Defaults to None.

        Raises:
            ValueError: if both 'relativeMediaItemId' and 'relativeEnrichmentItemId' is used
        """
    @staticmethod
    def from_dict(dct: dict):
        return AlbumPosition(
            position=dct["position"],
            relativeMediaItemId=dct["relativeMediaItemId"] if "relativeMediaItemId" in dct else None,
            relativeEnrichmentItemId=dct["relativeEnrichmentItemId"] if "relativeEnrichmentItemId" in dct else None
        )

    def __init__(self, position: PositionType = PositionType.FIRST_IN_ALBUM, *,
                 relativeMediaItemId: Optional[str] = None,
                 relativeEnrichmentItemId: Optional[str] = None) -> None:

        self.__position = position
        self.__relativeMediaItemId = None
        self.__relativeEnrichmentItemId = None
        if self.position in {PositionType.AFTER_MEDIA_ITEM, PositionType.AFTER_ENRICHMENT_ITEM}:
            if (not relativeMediaItemId and not relativeEnrichmentItemId) \
                    or (relativeEnrichmentItemId and relativeEnrichmentItemId):
                raise ValueError(
                    "Must supply exactly one between 'relativeMediaItemId' and 'relativeEnrichmentItemId'")
            if relativeMediaItemId:
                self.__relativeMediaItemId = relativeMediaItemId
            else:
                self.__relativeEnrichmentItemId = relativeEnrichmentItemId

    @property
    def position(self):
        """Type of position, for a media or enrichment item.
        """
        return self.__position

    @property
    def relativeMediaItemId(self):
        """The media item to which the position is relative to. 
        Only used when position type is AFTER_MEDIA_ITEM.
        """
        return self.__relativeMediaItemId

    @property
    def relativeEnrichmentItemId(self):
        """The enrichment item to which the position is relative to. 
        Only used when position type is AFTER_ENRICHMENT_ITEM.
        """
        return self.__relativeEnrichmentItemId


class Status(Dictable, Printable):
    """
    see https://developers.google.com/photos/library/reference/rest/v1/Status
    """
    @staticmethod
    def from_dict(dct: dict):
        return Status(
            message=dct["message"],
            code=dct["code"] if "code" in dct else None,
            details=dct["details"] if "details" in dct else None
        )

    def __init__(self, message: str, code: Optional[StatusCode] = None, details: Optional[list[dict]] = None) -> None:
        self.__message = message
        self.__code = code
        self.__details = details

    @property
    def message(self):
        """returns the Status's message
        """
        return self.__message

    @property
    def code(self):
        """returns the Status's code
        """
        return self.__code

    @property
    def details(self):
        """returns the Status's details
        """
        return self.__details


class MediaItemResult(Dictable, Printable):
    """Result of creating a new media item.

    Args:
        mediaItem (Optional[&quot;gpsdk.MediaItem&quot;], optional): 
            Media item created with the upload token. 
            It's populated if no errors occurred and the media item was created successfully. 
            Defaults to None.
        status (Optional[Status], optional): 
            If an error occurred during the creation of this media item, this field is populated with
            information related to the error. For details regarding this field, see Status. 
            Defaults to None.
        uploadToken (Optional[str], optional): 
            The upload token used to create this new (simple) media item.
            Only populated if the media item is simple and required a single upload token.
            Defaults to None.
    """
    @staticmethod
    def from_dict(dct: dict):
        return MediaItemResult(
            mediaItem=gpsdk.MediaItem.from_dict(
                gp=dct["gp"],
                dct=dct["mediaItem"]
            ) if "mediaItem" in dct else None,
            status=Status.from_dict(dct["status"]) if "status" in dct else None,  # noqa
            uploadToken=dct["uploadToken"] if "uploadToken" in dct else None,
        )

    def __init__(self, mediaItem: Optional["gpsdk.MediaItem"] = None, status: Optional[Status] = None,
                 uploadToken: Optional[str] = None) -> None:  # type:ignore

        self.__uploadToken = uploadToken
        self.__status = status
        self.__mediaItem = mediaItem

    @property
    def uploadToken(self):
        """The upload token used to create this new (simple) media item. 
        Only populated if the media item is simple and required a single upload token."""
        return self.__uploadToken

    @property
    def status(self):
        """If an error occurred during the creation of this media item, 
        this field is populated with information related to the error.
        For details regarding this field, see Status."""
        return self.__status

    @property
    def mediaItem(self):
        """Media item created with the upload token. 
        It's populated if no errors occurred and the media item was created successfully.
        """
        return self.__mediaItem


class MediaMetadata(Dictable, Printable):
    """Metadata for a media item.

    Args:
        creationTime (str): Time when the media item was first created (not when it was uploaded to Google Photos).
            A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits.
            Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".
        width (Optional[str], optional): Original width (in pixels) of the media item. Defaults to None.
        height (Optional[str], optional): Original height (in pixels) of the media item. Defaults to None.
        photo (Optional[dict], optional): Metadata for a photo media type. Defaults to None.
        video (Optional[dict], optional): Metadata for a video media type. Defaults to None.
    """
    @staticmethod
    def from_dict(dct: dict) -> "MediaMetadata":
        return MediaMetadata(
            creationTime=dct["creationTime"],
            width=dct["width"] if "width" in dct else None,
            height=dct["height"] if "height" in dct else None,
            photo=dct["photo"] if "photo" in dct else None,
            video=dct["video"] if "video" in dct else None,
        )

    def __init__(
        self,
        creationTime: str,
        width: Optional[str] = None,
        height: Optional[str] = None,
        photo: Optional[dict] = None,
        video: Optional[dict] = None
    ) -> None:
        FORMAT = "%Y-%m-%dT%H:%M:%SZ"
        try:
            self.__creationTime: datetime = datetime.strptime(creationTime, FORMAT)
        except ValueError:
            self.__creationTime: datetime = datetime.strptime(creationTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        self.__width: Optional[int] = int(width) if width else None
        self.__height: Optional[int] = int(height) if height else None
        self.__photo = photo
        self.__video = video

    @property
    def creationTime(self):
        """returns the MediaMetadata's creatingTime field
        """
        return self.__creationTime

    @property
    def width(self):
        """returns the MediaMetadata's width field
        """
        return self.__width

    @property
    def height(self):
        """returns the MediaMetadata's height field
        """
        return self.__height

    @property
    def photo(self):
        """returns the MediaMetadata's photo field
        """
        return self.__photo

    @property
    def video(self):
        """returns the MediaMetadata's video field
        """
        return self.__video


class ContributorInfo(Dictable, Printable):
    """Information about the user who added the media item.
    Note that this information is included only if the media item is within a shared album created by
    your app and you have the sharing scope.

    Args:
        profilePictureBaseUrl (str): URL to the profile picture of the contributor.
        displayName (str): Display name of the contributor.
    """
    @staticmethod
    def from_dict(dct: dict) -> "ContributorInfo":
        return ContributorInfo(
            profilePictureBaseUrl=dct["profilePictureBaseUrl"],
            displayName=dct["displayName"]
        )

    def __init__(self, profilePictureBaseUrl: str, displayName: str) -> None:

        self.__profilePictureBaseUrl = profilePictureBaseUrl
        self.__displayName = displayName

    @property
    def profilePictureBaseUrl(self) -> str:
        """returns the ContributorInfo's profilePictureBaseUrl field
        """
        return self.__profilePictureBaseUrl

    @property
    def displayName(self) -> str:
        """returns the ContributorInfo's displayName field
        """
        return self.__displayName


# class MultiPartEncoderWithProgress(MultipartEncoder):
#     def __init__(self, tqdm_options: dict, fields, boundary=None, encoding='utf-8'):
#         super().__init__(fields, boundary, encoding)
#         self.tqdm_options = tqdm_options

#     def _load(self, amount):
#         if not hasattr(self, "tqdm"):
#             setattr(self, "tqdm", tqdm(**self.tqdm_options))
#         MultipartEncoder._load(self, amount)
#         self.tqdm.update(amount/self.len * 100)  # pylint: disable=no-member


SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary',
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.sharing",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata"
]
EMPTY_PROMPT_MESSAGE = ""
DEFAULT_NUM_WORKERS: int = 2
ALBUMS_ENDPOINT = "https://photoslibrary.googleapis.com/v1/albums"
UPLOAD_MEDIA_ITEM_ENDPOINT = "https://photoslibrary.googleapis.com/v1/uploads"
MEDIA_ITEMS_CREATE_ENDPOINT = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
