import os
import pathlib
from typing import Iterable, Optional, Union, Generator
from requests.models import Response  # pylint: disable=import-error
import moviepy.editor as moviepy  # type:ignore
from .filters import SearchFilter
from ..gp import GooglePhotos
from ....utils import MediaItemMaskTypes, RequestType, AlbumPosition, NewMediaItem,\
    MediaItemResult, MediaMetadata, Printable, HeaderType, ProgressBar, ContributorInfo, OnlyPrivate, MimeType
from ....utils import MediaItemID, AlbumId, Path, NextPageToken, UploadToken
from ....utils import UPLOAD_MEDIA_ITEM_ENDPOINT, MEDIA_ITEMS_CREATE_ENDPOINT
from ....utils import slowdown, FileTime, FileTimeService
from ....utils import embed_mp4_creation_time

MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE: int = 25
MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE: int = 100
MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS: int = 50
DEFAULT_QUOTA: int = 30


class CoreMediaItem(Printable, OnlyPrivate):
    """The core wrapper class over the 'MediaItem' object

    Args:
        gp (GooglePhotos): Google Photos object
        id (MediaItemID): the id of the MediaItem
        productUrl (str): the utl to view this item in the browser
        mimeType (str): the type of the media
        mediaMetadata (dict | MediaMetadata): metadata
        filename (str): name of media
        baseUrl (str, optional): ?. Defaults to "".
        description (str, optional): media's description. Defaults to "".
    """
    SUPPORTED_VIDEO_FILE_TYPES = {".mov", ".mp4", ".wmv"}
    # ================================= STATIC HELPER METHODS =================================

    @staticmethod
    def _from_dict(gp: GooglePhotos, dct: dict) -> "CoreMediaItem":
        return CoreMediaItem(
            gp=gp,
            id=dct["id"],
            productUrl=dct["productUrl"],
            mimeType=dct["mimeType"],
            mediaMetadata=MediaMetadata.from_dict(dct["mediaMetadata"]),
            filename=dct["filename"],
            baseUrl=dct["baseUrl"] if "baseUrl" in dct else None,
            description=dct["description"] if "description" in dct else None,
            contributorInfo=ContributorInfo.from_dict(
                dct["ContributorInfo"]) if "ContributorInfo" in dct else None
        )

    @staticmethod
    @slowdown(60//DEFAULT_QUOTA)
    def upload_media(gp: GooglePhotos, media: Path, *, pbar: Optional[ProgressBar] = None) -> UploadToken:
        """uploads a single media item to Google's servers
        NOTE: This does not add it to your library!
        NOTE: To add the media to your library, you need to use MediaItem.batchCreate afterwards
            or just use MediaItem.add_to_library instead

        Args:
            gp (GooglePhotos): Google Photos Object
            media (Path): the path to the media
            pbar (Optional[ProgressBar]): An instance of a class implementing ProgressBar to show an 
                optional progress bar while uploading. tqdm is okay.

        Raises:
            HTTPError: If the HTTP request has failed

        Returns:
            UploadToken: the upload token to pass to be used in other functions
        """
        header_type = HeaderType.JSON
        # TODO add more options
        file_extension = pathlib.Path(media).suffix.lower()
        additional_headers: dict = {
            "X-Goog-Upload-Protocol": "raw"
        }
        new_path = media  # assign default value
        copied_times: Optional[FileTime] = None
        if file_extension in CoreMediaItem.SUPPORTED_VIDEO_FILE_TYPES:
            if file_extension != '.mp4':
                p = pathlib.Path(media)
                new_path = os.path.join(p.parent, f'{p.stem}.mp4')
                if not os.path.exists(new_path):
                    if pbar is not None:
                        pbar.write(
                            f"Video is not MP4. Creating {new_path}."
                            "\nThis may take a while depending on the length of the video"
                        )
                    clip = moviepy.VideoFileClip(media)
                    clip.write_videofile(new_path, verbose=False, logger=None)
                    copied_times = FileTimeService().get(media)
                    # Photos uses container creation_time from the uploaded bytes,
                    # not filesystem mtime — stamp before reading the payload.
                    stamp = (
                        copied_times.modification
                        or copied_times.access
                        or copied_times.creation
                    )
                    if stamp is not None:
                        embed_mp4_creation_time(new_path, stamp)
            header_type = HeaderType.OCTET
            additional_headers["X-Goog-Upload-Content-Type"] = MimeType.MP4.value
        with open(new_path, 'rb') as data_stream:
            payload = data_stream.read()
        # After the read: Windows updates atime on open. Apply source atime/mtime last.
        if copied_times is not None:
            FileTimeService().set(
                new_path,
                FileTime(access=copied_times.access, modification=copied_times.modification),
            )
        response = gp.request(
            RequestType.POST,
            UPLOAD_MEDIA_ITEM_ENDPOINT,
            header_type=header_type,
            pbar=pbar,
            data=payload,
            additional_headers=additional_headers
        )
        response.raise_for_status()
        token = response.content.decode('utf-8')
        return token

    # ================================= API METHODS =================================
    @staticmethod
    def batchCreate(
            gp: GooglePhotos, newMediaItems: Iterable[NewMediaItem], albumId: Optional[AlbumId] = None,
        albumPosition: Optional[AlbumPosition] = None) \
            -> list[MediaItemResult]:
        """Creates one or more media items in a user's Google Photos library.
            This is the second step for creating a media item.\n
            For details regarding Step 1, uploading the raw bytes to a Google Server, see GPMediaItem.upload_media\n
            This call adds the media item to the library.
            If an album id is specified, the call adds the media item to the album too. 
            Each album can contain up to 20,000 media items. 
            By default, the media item will be added to the end of the library or album.
            If an album id and position are both defined, the media item is added to the album at the
                specified position.
            If the call contains multiple media items, they're added at the specified position. 
            If you are creating a media item in a shared album where you are not the owner, you are not allowed
                to position the media item.
            Doing so will result in a BAD REQUEST error.
        Args:
            gp (GooglePhotos): the Google Photos object
            newMediaItems (Iterable[NewMediaItem]): Required. List of media items to be created. 
                Maximum 50 media items per call.
            albumId (Optional[AlbumId]): Identifier of the album where the media items are added. 
                The media items are also added to the user's library. This is an optional field.
            albumPosition (Optional[]): Position in the album where the media items are added. 
                If not specified, the media items are added to the end of the album 
                (as per the default value, that is, LAST_IN_ALBUM). 
                The request fails if this field is set and the albumId is not specified. 
                The request will also fail if you set the field and are not the owner of the shared album.
        Raises:
            ValueError: If the optional arguments are passed incorrectly
            HTTPError: If the HTTP request has failed

        Yields:
            Generator[NewMediaItemResult, None, None]: A generator of wrapper objects representing
                the contents of the response.
        """
        # TODO: If you are creating a media item in a shared album where you are not the owner,
        # you are not allowed to position the media item. Doing so will result in a BAD REQUEST error.
        if not (0 <= len(list(newMediaItems)) <= MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS):  # pylint: disable=unneeded-not,superfluous-parens
            raise ValueError(
                f"'newMediaItems' can only hold a maximum of {MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS} items per call")
        body: dict[str, Union[str, list, dict]] = {
            # see https://developers.google.com/photos/library/reference/rest/v1/mediaItems/batchCreate
            "newMediaItems": [item.to_dict() for item in newMediaItems]
        }
        if albumId:
            body["albumId"] = albumId
        if albumPosition:
            if not albumId:
                raise ValueError(
                    "'albumPosition' is only valid if 'albumId' is also passed together")
            body["albumPosition"] = albumPosition.to_dict()

        response = gp.request(
            RequestType.POST,
            MEDIA_ITEMS_CREATE_ENDPOINT,
            json=body
        )
        response.raise_for_status()
        media_items = []
        for dct in response.json()["newMediaItemResults"]:
            dct["gp"] = gp
            media_items.append(MediaItemResult.from_dict(dct))
        return media_items

    @staticmethod
    def batchGet(gp: GooglePhotos, ids: Iterable[str]
                 ) -> Generator[MediaItemResult, None, None]:
        """Returns the list of media items for the specified media item identifiers. 
            Items are returned in the same order as the supplied identifiers.

        Args:
            gp (GooglePhotos): Google Photos object
            ids (Iterable[str]): Returns the list of media items for the specified media item identifiers. 
                Items are returned in the same order as the supplied identifiers.

        Raises:
            HTTPError: If the HTTP request has failed

        Yields:
            Generator[MediaItemResult, None, None]: _description_
        """
        ENDPOINT = "https://photoslibrary.googleapis.com/v1/mediaItems:batchGet"
        params = {
            "mediaItemIds": ids
        }
        response = gp.request(
            RequestType.GET,
            ENDPOINT,
            HeaderType.DEFAULT,
            params=params,
        )

        response.raise_for_status()
        for dct in response.json()["mediaItemResults"]:
            dct["gp"] = gp
            yield MediaItemResult.from_dict(dct)

    @staticmethod
    def get(gp: GooglePhotos, mediaItemId: str) -> Response:
        """Returns the media item for the specified media item identifier.

        Args:
            gp (gpsdk.gp.GooglePhotos): Google Photos object
            mediaItemId (str): the id of the wanted item

        Raises:
            HTTPError: if the request fails

        Returns:
            GPMediaItem: the resulting object
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/mediaItems/{mediaItemId}"
        response = gp.request(RequestType.GET, endpoint)
        response.raise_for_status()
        return response  # GPMediaItem.from_dict(gp, response.json())

    @staticmethod
    def search(
            gp: GooglePhotos,
            albumId: Optional[str] = None,
            pageSize: int = 25,
            pageToken: Optional[str] = None,
            filters: Optional[SearchFilter] = None,
            orderBy: Optional[str] = None
    ) -> tuple[Generator["CoreMediaItem", None, None], Optional[NextPageToken]]:
        """Searches for media items in a user's Google Photos library. 
        If no filters are set, then all media items in the user's library are returned. 
        If an album is set, all media items in the specified album are returned. 
        If filters are specified, media items that match the filters from the user's library are listed. 
        If you set both the album and the filters, the request results in an error.

        Args:
            gp (gpsdk.objects.core.gp.CoreGooglePhotos): _description_
            albumId (Optional[str], optional): Identifier of an album. 
                If populated, lists all media items in specified album. 
                Can't set in conjunction with any filters. Defaults to None.
            pageSize (int, optional): Maximum number of media items to return in the response. 
                Fewer media items might be returned than the specified number. 
                The default pageSize is 25, the maximum is 100. Defaults to 25.
            pageToken (Optional[str], optional): A continuation token to get the next page of the results. 
                Adding this to the request returns the rows after the pageToken. 
                The pageToken should be the value returned in the nextPageToken parameter 
                in the response to the searchMediaItems request. Defaults to None.
            filters (Optional[SearchFilter], optional): Filters to apply to the request. 
                Can't be set in conjunction with an albumId. Defaults to None.
            orderBy (Optional[str], optional): An optional field to specify the sort order of the search results.
                The orderBy field only works when a dateFilter is used. 
                When this field is not specified, results are displayed newest first, oldest last by their creationTime. 
                Providing MediaMetadata.creation_time displays search results in the 
                    opposite order, oldest first then newest last. 
                To display results newest first then oldest last, include the desc
                    argument as follows: MediaMetadata.creation_time desc.
                The only additional filters that can be used with this parameter are
                    includeArchivedMedia and excludeNonAppCreatedData. 
                No other filters are supported. Defaults to None.

        Raises:
            ValueError: 'albumId' cannot be set in conjunction with 'filters'
            ValueError: 'pageSize' must be a positive integer. maximum value: 100
            ValueError: The 'orderBy' field only works when a 'dateFilter' is used.
            HTTPError: If the HTTP request has failed

        Returns:
            tuple[list[dict], Optional[NextPageToken]]: a list of the resulting objects, token for next request.
        """
        if albumId and filters:
            raise ValueError(
                "'albumId' cannot be set in conjunction with 'filters'")
        if not (0 < pageSize <= 100):  # pylint: disable=unneeded-not,superfluous-parens
            raise ValueError(
                "'pageSize' must be a positive integer. maximum value: 100")
        endpoint = "https://photoslibrary.googleapis.com/v1/mediaItems:search"
        payload: dict = {
            "pageSize": pageSize
        }

        if albumId:
            payload["albumId"] = albumId

        if pageToken:
            payload["pageToken"] = pageToken

        if filters:
            payload["filters"] = {}
            if filters.contentFilter:
                payload["filters"]["contentFilter"] = filters.contentFilter.to_dict()

            if filters.dateFilter:
                payload["filters"]["dateFilter"] = filters.dateFilter.to_dict()

            if filters.featureFilter:
                payload["filters"]["featureFilter"] = filters.featureFilter.to_dict()

            if filters.mediaTypeFilter:
                payload["filters"]["mediaTypeFilter"] = filters.mediaTypeFilter.to_dict()

        if orderBy:
            if not filters or not filters.dateFilter:
                raise ValueError(
                    "The 'orderBy' field only works when a 'dateFilter' is used.")
            # TODO implement this
            # payload["orderBy"] = ?

        response = gp.request(RequestType.POST, endpoint, json=payload)
        response.raise_for_status()
        j = response.json()
        mediaItems = j["mediaItems"] if "mediaItems" in j else []
        nextPageToken = j["nextPageToken"] if "nextPageToken" in j else None
        return (CoreMediaItem._from_dict(gp, dct)
                for dct in mediaItems), nextPageToken

    @staticmethod
    def list(gp: GooglePhotos, pageSize: int = MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE,
             pageToken: Optional[str] = None) -> tuple[list["CoreMediaItem"], Optional[NextPageToken]]:
        """List all media items from a user's Google Photos library.

        Args:
            gp (GooglePhotos): Google Photos object
            pageSize (int, optional): Maximum number of media items to return in the response. 
                Fewer media items might be returned than the specified number. 
                The default pageSize is MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE, 
                the maximum is MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE. Defaults to MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE.
            pageToken (Optional[str], optional): A continuation token to get the next page of the results. 
                Adding this to the request returns the rows after the pageToken. 
                The pageToken should be the value returned in the nextPageToken parameter in the 
                response to the listMediaItems request. Defaults to None.

        Raises:
            ValueError: if pageSize is in the correct value range

        Returns:
            tuple[list[dict], Optional[NextPageToken]]: _description_
        """
        if not (0 < pageSize <= MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE):  # pylint: disable=unneeded-not,superfluous-parens
            raise ValueError(
                f"pageSize must be between 0 and {MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE}.\n"
                "see https://developers.google.com/photos/library/reference/rest/v1/mediaItems/list#query-parameters")
        endpoint = "https://photoslibrary.googleapis.com/v1/mediaItems"
        params: dict = {
            "pageSize": pageSize
        }
        if pageToken:
            params["pageToken"] = pageToken
        response = gp.request(
            RequestType.GET,
            endpoint,
            HeaderType.DEFAULT,
            params=params
        )
        response.raise_for_status()
        j = response.json()
        mediaItems = j["mediaItems"] if "mediaItems" in j else []
        nextPageToken = j["nextPageToken"] if "nextPageToken" in j else None
        return [CoreMediaItem._from_dict(gp, dct) for dct in mediaItems], nextPageToken

    def patch(self, mask_type: MediaItemMaskTypes, field_value: str) -> Response:
        """Update the media item with the specified id. Only the id and description fields of the media item are read. 
            The media item must have been created by the developer via the API and must be owned by the user.

        Args:
            mask_type (MediaItemMaskTypes): Required. Indicate what fields in the provided media item to update.
            field_value (str): the new value for said field

        Raises:
            HTTPError: If the HTTP request has failed

        Returns:
            Response: the response of the request
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/mediaItems/{self.id}"
        payload = {
            mask_type.value: field_value
        }
        params = {
            "updateMask": mask_type.value
        }
        response = self.gp.request(
            RequestType.PATCH, endpoint, json=payload, params=params)
        response.raise_for_status()
        return response

    # ================================= INSTANCE METHODS =================================
    def __init__(
            self,
            gp: GooglePhotos,
            id: MediaItemID,  # pylint: disable=redefined-builtin
            productUrl: str,
            mimeType: str,
            mediaMetadata: Union[dict, MediaMetadata],
            filename: str,
            baseUrl: Optional[str] = None,
            description: Optional[str] = None,
            contributorInfo: Optional[ContributorInfo] = None,
    ) -> None:
        self.gp = gp
        self.id = id
        self.productUrl = productUrl
        self.mimeType = mimeType
        self.mediaMetadata: MediaMetadata = mediaMetadata if isinstance(
            mediaMetadata, MediaMetadata) else MediaMetadata.from_dict(mediaMetadata)
        self.filename = filename
        self.baseUrl = baseUrl
        self.description = description
        self.contributorInfo = contributorInfo

    def __eq__(self, other) -> bool:
        if not isinstance(other, CoreMediaItem):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


__all__ = [
    "CoreMediaItem",
    "MediaItemID",
    "MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE",
    "MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE",
    "MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS"
]
