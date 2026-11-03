from typing import Optional, Iterable, Generator
from requests import Response
from .gp import GooglePhotos
from .media_item import MediaItemID
from .enrichment_item import CoreEnrichmentItem
from ...utils import PositionType, EnrichmentType, RequestType, Printable, AlbumMaskType, HeaderType,\
    OnlyPrivate
from ...utils import AlbumId, NextPageToken
from ...utils import ALBUMS_ENDPOINT


class CoreAlbum(Printable, OnlyPrivate):
    """the basic wrapper class over 'Album' object
     Args:
            gp (GooglePhotos): Google Photos object
            id (AlbumId): the id of the Album
            title (str): the title of the Album
            productUrl (str): the url to view the Album
            isWriteable (bool): if it is possible to edit the album
            mediaItemsCount (int): how many MediaItems are there in the album
            coverPhotoBaseUrl (str): the url to the cover photo
            coverPhotoMediaItemId (MediaItemID): the id of the media item which is the cover photo
    """
    # ================================= HELPER STATIC METHODS =================================
    @staticmethod
    def _from_dict(gp: GooglePhotos, dct: dict) -> "CoreAlbum":
        """creates a GooglePhotosAlbum object from a dict from a response object

        Args:
            gp (gp_wrapper.gp.GooglePhotos): the GooglePhotos object
            dct (dict): the dict object containing the data

        Returns:
            GooglePhotosAlbum: the resulting object
        """
        return CoreAlbum(
            gp,
            id=dct["id"],
            title=dct["title"],
            productUrl=dct["productUrl"],
            isWriteable=dct["isWriteable"] if "isWriteable" in dct else None,
            mediaItemsCount=int(dct["mediaItemsCount"]
                                ) if "mediaItemsCount" in dct else 0,
            coverPhotoBaseUrl=dct["coverPhotoBaseUrl"] if "coverPhotoBaseUrl" in dct else None,
            coverPhotoMediaItemId=dct["coverPhotoMediaItemId"] if "coverPhotoMediaItemId" in dct else None,
        )
    # ================================= INSTANCE METHODS =================================

    def __init__(
        self,
        gp: GooglePhotos,
        id: AlbumId,  # pylint: disable=redefined-builtin
        title: str,
        productUrl: str,
        isWriteable: Optional[bool] = None,
        mediaItemsCount: int = 0,
        coverPhotoBaseUrl: Optional[str] = None,
        coverPhotoMediaItemId: Optional[MediaItemID] = None
    ) -> None:
        self.gp = gp
        self.id = id
        self.title = title
        self.productUrl = productUrl
        self.isWriteable = isWriteable
        self.mediaItemsCount = mediaItemsCount
        self.coverPhotoBaseUrl = coverPhotoBaseUrl
        self.coverPhotoMediaItemId = coverPhotoMediaItemId

    def __eq__(self, other) -> bool:
        if not isinstance(other, CoreAlbum):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # ================================= INSTANCE API METHODS =================================

    def addEnrichment(self, enrichment_type: EnrichmentType, enrichment_data: dict,
                      album_position: PositionType, album_position_data: Optional[dict] = None)\
            -> tuple[Optional[Response], Optional[CoreEnrichmentItem]]:
        """Adds an enrichment at a specified position in a defined album.

        Args:
            enrichment_type (EnrichmentType): the type of the enrichment
            enrichment_data (dict): the data for the enrichment
            album_position (ALbumPosition): where to add the enrichment
            album_position_data (Optional[dict], optional): additional data maybe required for some of the options.
                Defaults to None.

        Returns:
            EnrichmentItem: the item added
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{self.id}:addEnrichment"
        body: dict[str, dict] = {
            "newEnrichmentItem": {
                enrichment_type.value: enrichment_data
            },
            "albumPosition": {
                "position": album_position.value
            }
        }
        if album_position_data is not None:
            body["albumPosition"].update(album_position_data)

        response = self.gp.request(RequestType.POST, endpoint, json=body)
        try:
            return None, CoreEnrichmentItem(response.json()["enrichmentItem"]["id"])
        except:
            return response, None

    def batchAddMediaItems(self, ids: Iterable[MediaItemID]) -> Response:
        """Adds one or more media items in a user's Google Photos library to an album. 
        The media items and albums must have been created by the developer via the API.
        Media items are added to the end of the album. 
        If multiple media items are given, they are added in the order specified in this call.
        Each album can contain up to 20,000 media items.
        Only media items that are in the user's library can be added to an album. 
        For albums that are shared, the album must either be owned by the user or the user must have joined
            the album as a collaborator.
        Partial success is not supported. The entire request will fail if an invalid media item or album is specified.

        Args:
            ids (Iterable[MediaItemID]): paths to media files

        Returns:
            Response: the response of the request
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{self.id}:batchAddMediaItems"
        payload: dict = {
            "mediaItemIds": list(ids)
        }
        response = self.gp.request(RequestType.POST, endpoint, json=payload)
        return response

    def batchRemoveMediaItems(self, ids: Iterable[MediaItemID]) -> Response:
        """Removes one or more media items from a specified album.
        The media items and the album must have been created by the developer via the API.
        For albums that are shared, this action is only supported for media items that were added to the album
            by this user, or for all media items if the album was created by this user.
        Partial success is not supported. The entire request will fail and no action will be performed on
            the album if an invalid media item or album is specified.

        Args:
            ids (Iterable[MediaItemID]): paths to media files

        Returns:
            Response: the response of the request
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{self.id}:batchAddMediaItems"
        payload: dict = {
            "mediaItemIds": list(ids)
        }
        response = self.gp.request(RequestType.POST, endpoint, json=payload)
        return response

    def patch(self, mask_type: AlbumMaskType, field_value) -> Response:
        """Update the album with the specified id. 
        Only the id, title and coverPhotoMediaItemId fields of the album are read.
        The album must have been created by the developer via the API and must be owned by the user.

        Args:
            mask_type (AlbumMaskType): _description_
            field_value (_type_): _description_

        Returns:
            Response: _description_
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{self.id}"
        payload = {
            mask_type.value: field_value
        }
        params = {
            "updateMask": mask_type.value
        }
        response = self.gp.request(
            RequestType.PATCH, endpoint, json=payload, params=params)
        return response

    def share(self, isCollaborative: bool = True, isCommentable: bool = True) -> Response:
        """share an album

        Args:
            isCollaborative (bool, optional): whether to allow other people to also edit the album. Defaults to True.
            isCommentable (bool, optional): whether to allow other people to comment. Defaults to True.

        Returns:
            Response: _description_
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{self.id}:addEnrichment"
        body = {
            "sharedAlbumOptions": {
                "isCollaborative": isCollaborative,
                "isCommentable": isCommentable
            }
        }
        response = self.gp.request(
            RequestType.POST, endpoint, json=body)
        return response

    def unshare(self) -> Response:
        """make a shared album private

        Returns:
            Response: resulting response
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{self.id}:unshare"
        response = self.gp.request(
            RequestType.POST,
            endpoint,
            HeaderType.DEFAULT
        )
        return response
    # ================================= STATIC API METHODS =================================

    @staticmethod
    def create(gp: GooglePhotos, album_name: str) -> "CoreAlbum":
        """Creates an album in a user's Google Photos library.
        see https://developers.google.com/photos/library/reference/rest/v1/albums/create
        Args:
            gp (CoreGooglePhotos): Google Photos object
            album_name (str): name of new album

        Returns:
            CoreGPAlbum: the album object
        """
        payload = {
            "album": {
                "title": album_name
            }
        }
        response = gp.request(
            RequestType.POST,
            ALBUMS_ENDPOINT,
            json=payload,
        )
        dct = response.json()
        album = CoreAlbum._from_dict(gp, dct)
        return album

    @staticmethod
    def get(gp: GooglePhotos, albumId: str) -> Optional["CoreAlbum"]:
        """Returns the album based on the specified albumId.
        The albumId must be the ID of an album owned by the user or a shared album that the user has joined.

        Args:
            gp (CoreGooglePhotos): Google Photos object
            albumId (str): the desired album's id

        Raises:
            HTTPError: if the request fails for some reason

        Returns:
            CoreGPAlbum: the desired album
        """
        endpoint = f"https://photoslibrary.googleapis.com/v1/albums/{albumId}"
        response = gp.request(
            RequestType.GET,
            endpoint,
            HeaderType.DEFAULT
        )
        if response.status_code not in {200, 400}:
            response.raise_for_status()
        if response.status_code == 200:
            return CoreAlbum._from_dict(gp, response.json())
        return None

    @staticmethod
    def list(
        gp: GooglePhotos,
        pageSize: int = 20,
        prevPageToken: Optional[NextPageToken] = None,
        excludeNonAppCreatedData: bool = False
    ) -> tuple[Optional[Generator["CoreAlbum", None, None]], Optional[NextPageToken]]:
        """Lists all albums shown to a user in the Albums tab of the Google Photos app.

        pageSize (int): Maximum number of albums to return in the response.
            Fewer albums might be returned than the specified number. The default pageSize is 20, the maximum is 50.
        pageToken (str): A continuation token to get the next page of the results.
            Adding this to the request returns the rows after the pageToken.
            The pageToken should be the value returned in the nextPageToken parameter in the response
            to the listAlbums request.
        excludeNonAppCreatedData (bool): If set, the results exclude media items that were not created by this app.
            Defaults to false (all albums are returned).
            This field is ignored if the photoslibrary.readonly.appcreateddata scope is used.

        Returns:
            tuple[Generator[CoreGPAlbum, None, None], Optional[NextPageToken]]: 
                - a generator with CoreGPAlbum objects
                - a token to supply to a future call to get albums after current end point in album list

        """

        endpoint = "https://photoslibrary.googleapis.com/v1/albums"
        payload: dict = {
            "pageSize": pageSize,
            "excludeNonAppCreatedData": excludeNonAppCreatedData
        }
        if prevPageToken is not None:
            payload["pageToken"] = prevPageToken
        response = gp.request(
            RequestType.GET,
            endpoint,
            HeaderType.DEFAULT,
            params=payload,
        )
        response.raise_for_status()
        j = response.json()
        token: Optional[NextPageToken] = None
        gen: Optional[Generator[CoreAlbum, None, None]] = []  # type:ignore
        if j:
            if "nextPageToken" in j:
                token = j["nextPageToken"]
            if "albums" in j:
                gen = (CoreAlbum._from_dict(gp, dct) for dct in j["albums"])
        return gen, token
