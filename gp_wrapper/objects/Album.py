import pathlib
from typing import Optional, Generator, Iterable
from requests.models import Response  # type:ignore
from .core import GooglePhotos, CoreAlbum, CoreEnrichmentItem
from .MediaItem import MediaItem
from ..utils import PositionType, EnrichmentType, RequestType, AlbumMaskType, \
    NewMediaItem, SimpleMediaItem, MediaItemResult, batchify
from ..utils import Path, NextPageToken


class Album(CoreAlbum):
    """the advanced wrapper class over 'Album' object
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
    def _from_core(obj: CoreAlbum) -> "Album":
        return Album(
            gp=obj.gp,
            id=obj.id,
            title=obj.title,
            productUrl=obj.productUrl,
            isWriteable=obj.isWriteable,
            mediaItemsCount=obj.mediaItemsCount,
            coverPhotoBaseUrl=obj.coverPhotoBaseUrl,
            coverPhotoMediaItemId=obj.coverPhotoMediaItemId
        )

    # ================================= OVERRIDDEN STATIC METHODS =================================
    @staticmethod
    def get(gp: GooglePhotos, albumId: str) -> Optional["Album"]:
        core = CoreAlbum.get(gp, albumId)
        if not core:
            return None
        return Album._from_core(core)

    @staticmethod
    def create(gp: GooglePhotos, album_name: str) -> "Album":
        return Album._from_core(CoreAlbum.create(gp, album_name))

    # ================================= ADDITIONAL STATIC METHODS =================================

    @staticmethod
    def all_albums(
        gp: GooglePhotos,
        pageSize: int = 20,
        prevPageToken: Optional[NextPageToken] = None,
        excludeNonAppCreatedData: bool = False
    ) -> Generator["Album", None, None]:
        """gets all albums serially
        Args:
            pageSize (int): Maximum number of albums to return in the response.
                Fewer albums might be returned than the specified number. The default pageSize is 20, the maximum is 50.
            pageToken (str): A continuation token to get the next page of the results.
                Adding this to the request returns the rows after the pageToken.
                The pageToken should be the value returned in the nextPageToken parameter in the response
                to the listAlbums request.
            excludeNonAppCreatedData (bool): If set, the results exclude media items that were not created by this app.
                Defaults to false (all albums are returned).
                This field is ignored if the photoslibrary.readonly.appcreateddata scope is used.
        Raises:
            HTTPError: if the request fails

        Returns:
            Generator[Album, None, None]: a generator of Album objects
        """
        gen, prevPageToken = Album.list(
            gp, pageSize, None, excludeNonAppCreatedData)
        if gen:
            yield from (Album._from_core(g) for g in gen)
        while prevPageToken:
            gen, prevPageToken = Album.list(
                gp, pageSize, prevPageToken, excludeNonAppCreatedData)
            if gen:
                yield from (Album._from_core(g) for g in gen)

    @staticmethod
    def exists(
            gp: GooglePhotos,
            name: Optional[str] = None,
            id: Optional[str] = None  # pylint: disable=redefined-builtin
    ) -> Optional["Album"]:
        """checks whether an album exists, if so - returns it

        *supply only one
        Args:
            name (Optional[str]): supply a name to get first album with this name [NOT EFFICIENT]
            id (Optional[str]): supply id to get album with this exact id [EFFICIENT]
        Raises:
            ValueError: if both identifiers are used

        Returns:
             Optional[GPAlbum]: returns the album if it exists or None
        """
        if id is not None and name is not None:
            raise ValueError("must use only one between 'id' and 'name'")
        if id is not None:
            core = Album.get(gp, id)
            if core:
                return core
            return None
        for album in Album.all_albums(gp):
            if name:
                if album.title == name:
                    return album
        return None

    @staticmethod
    def from_dict(gp: GooglePhotos, dct: dict) -> "Album":
        """creates a GooglePhotosAlbum object from a dict from a response object

        Args:
            gp (gp_wrapper.gp.GooglePhotos): the GooglePhotos object
            dct (dict): the dict object containing the data

        Returns:
            GooglePhotosAlbum: the resulting object
        """
        return Album(
            gp,
            id=dct["id"],
            title=dct["title"],
            productUrl=dct["productUrl"],
            isWriteable=dct["isWriteable"],
            mediaItemsCount=int(dct["mediaItemsCount"]
                                ) if "mediaItemsCount" in dct else 0,
            coverPhotoBaseUrl=dct["coverPhotoBaseUrl"] if "coverPhotoBaseUrl" in dct else "",
            coverPhotoMediaItemId=dct["coverPhotoMediaItemId"] if "coverPhotoMediaItemId" in dct else "",
        )

    # ================================= ADDITIONAL INSTANCE METHODS =================================
    def add_text(
        self,
        description_parts: Iterable[str],
        relative_position: PositionType = PositionType.FIRST_IN_ALBUM,
        optional_additional_data: Optional[dict] = None
    ) -> Iterable[tuple[Optional[Response], Optional[CoreEnrichmentItem]]]:
        """a facade function that uses 'add_enrichment' to simplify adding a description

        Args:
            description (str): description to add
            relative_position (ALbumPosition, optional): where to add the description.
                Defaults to ALbumPosition.FIRST_IN_ALBUM.

        Returns:
            EnrichmentItem: the resulting item
        """
        HARD_LIMIT: int = 1000
        # copy the items if it is a generator
        parts = list(description_parts)
        for part in parts:
            if len(part) > HARD_LIMIT:
                raise ValueError(
                    f"the description parts should be less than {HARD_LIMIT} characters"
                    "long because of a hard limit google employs")
        chunks: list[str] = []
        tmp_chunk = ""
        for text in parts:
            if len(tmp_chunk) + len(text) >= 1000:
                chunks.append(tmp_chunk)
                tmp_chunk = ""
            tmp_chunk += text

        if len(tmp_chunk) > 0:
            chunks.append(tmp_chunk)

        items = []
        for part in chunks[::-1]:
            items.append(self.addEnrichment(
                EnrichmentType.TEXT_ENRICHMENT,
                {"text": part},
                relative_position,
                album_position_data=optional_additional_data
            ))
        return items

    def get_media(self) -> Iterable[MediaItem]:
        """gets all media in album

        Returns:
            Iterable[GooglePhotosMediaItem]: all media of the album

        Yields:
            Iterator[Iterable[GooglePhotosMediaItem]]: _description_
        """
        endpoint = "https://photoslibrary.googleapis.com/v1/mediaItems:search"
        data = {
            "albumId": self.id
        }
        response = self.gp.request(
            RequestType.POST, endpoint, json=data)
        if not response.status_code == 200:
            return []
        j = response.json()
        if "mediaItems" not in j:
            return []
        res = []
        for dct in j["mediaItems"]:
            res.append(MediaItem.from_dict(self.gp, dct))
        return res

    def set_title(self, new_title: str) -> Response:
        """sets the title of an album

        Args:
            new_title (str): new title to set to

        Returns:
            Response: response of this request
        """
        res = self.patch(AlbumMaskType.TITLE, new_title)
        if res.status_code == 200:
            self.title = new_title
        return res

    def upload_and_add(
        self,
        paths: Iterable[Path]
    ) -> list[MediaItemResult]:
        """uploads the media to the library and also adds them to current album

        Args:
            paths (Iterable[Path]): paths to media files

        Returns:
            list[MediaItemResult]: resulting objects of the uploads
        """
        # same code as MediaItem.add_to_library but it is more memory efficient this way
        items: list[NewMediaItem] = []
        for path in paths:
            token = MediaItem.upload_media(self.gp, path)
            filename = pathlib.Path(path).stem
            item = NewMediaItem("", SimpleMediaItem(token, filename))
            items.append(item)
        batches: list[list[NewMediaItem]] = []
        batch: list[NewMediaItem] = []
        for item in items:
            if len(batch) >= 50:
                batches.append(batch)
                batch = []
            batch.append(item)
        batches.append(batch)
        res = []
        for batch in batches:
            res.extend(MediaItem.batchCreate(self.gp, batch, self.id))
        return res


__all__ = [
    "Album",
    "PositionType",
    "EnrichmentType"
]
