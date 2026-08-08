"""Tests for CoreAlbum and Album."""
from __future__ import annotations

import pytest
from requests import HTTPError

from gp_wrapper.objects.Album import Album
from gp_wrapper.objects.MediaItem import MediaItem
from gp_wrapper.objects.core.album import CoreAlbum
from gp_wrapper.objects.core.enrichment_item import CoreEnrichmentItem
from gp_wrapper.utils.structures.data_types import MediaItemResult
from gp_wrapper.utils.structures.enums import AlbumMaskType, EnrichmentType, PositionType

from .conftest import ALBUM_DICT, ALBUM_DICT_MINIMAL, MEDIA_ITEM_DICT, make_response


def _album(gp, dct=None) -> Album:
    return Album._from_core(CoreAlbum._from_dict(gp, dct or ALBUM_DICT))


def test_core_album_from_dict_full_and_minimal(gp) -> None:
    full = CoreAlbum._from_dict(gp, ALBUM_DICT)
    assert full.id == "album-1"
    assert full.mediaItemsCount == 3
    assert full.isWriteable is True
    minimal = CoreAlbum._from_dict(gp, ALBUM_DICT_MINIMAL)
    assert minimal.mediaItemsCount == 0
    assert minimal.isWriteable is None
    assert minimal.coverPhotoBaseUrl is None
    assert minimal.coverPhotoMediaItemId is None


def test_core_album_eq_hash(gp) -> None:
    a = CoreAlbum._from_dict(gp, ALBUM_DICT)
    b = CoreAlbum._from_dict(gp, ALBUM_DICT)
    other = CoreAlbum._from_dict(gp, ALBUM_DICT_MINIMAL)
    assert a == b
    assert a != other
    assert a != "album-1"
    assert hash(a) == hash("album-1")
    assert str(a)


def test_add_enrichment_success_and_failure(gp) -> None:
    album = _album(gp)
    gp.session.post.return_value = make_response(
        {"enrichmentItem": {"id": "enr-9"}}
    )
    err, item = album.addEnrichment(
        EnrichmentType.TEXT_ENRICHMENT,
        {"text": "hello"},
        PositionType.FIRST_IN_ALBUM,
    )
    assert err is None
    assert isinstance(item, CoreEnrichmentItem)
    assert item.id == "enr-9"

    gp.session.post.return_value = make_response({"error": "bad"})
    err, item = album.addEnrichment(
        EnrichmentType.LOCATION_ENRICHMENT,
        {"location": {"name": "x"}},
        PositionType.LAST_IN_ALBUM,
        album_position_data={"extra": 1},
    )
    assert item is None
    assert err is not None


def test_batch_add_and_remove_and_patch_share_unshare(gp) -> None:
    album = _album(gp)
    gp.session.post.return_value = make_response({})
    gp.session.patch.return_value = make_response({})
    assert album.batchAddMediaItems(["m1", "m2"]).status_code == 200
    assert album.batchRemoveMediaItems(["m1"]).status_code == 200
    assert album.patch(AlbumMaskType.TITLE, "New").status_code == 200
    assert album.share(isCollaborative=False, isCommentable=True).status_code == 200
    assert album.unshare().status_code == 200


def test_create_and_get(gp) -> None:
    gp.session.post.return_value = make_response(ALBUM_DICT)
    created = CoreAlbum.create(gp, "Test Album")
    assert created.title == "Test Album"

    gp.session.get.return_value = make_response(ALBUM_DICT, status_code=200)
    got = CoreAlbum.get(gp, "album-1")
    assert got is not None and got.id == "album-1"

    gp.session.get.return_value = make_response({}, status_code=400)
    assert CoreAlbum.get(gp, "missing") is None

    err = make_response({}, status_code=500)
    err.raise_for_status.side_effect = HTTPError("boom")
    gp.session.get.return_value = err
    with pytest.raises(HTTPError):
        CoreAlbum.get(gp, "broken")


def test_list_albums_variants(gp) -> None:
    gp.session.get.return_value = make_response(
        {"albums": [ALBUM_DICT, ALBUM_DICT_MINIMAL], "nextPageToken": "tok-2"}
    )
    gen, token = CoreAlbum.list(gp, pageSize=10, prevPageToken="tok-1")
    assert token == "tok-2"
    albums = list(gen)
    assert albums[0].id == "album-1"
    assert albums[1].id == "album-min"

    gp.session.get.return_value = make_response({})
    gen, token = CoreAlbum.list(gp, excludeNonAppCreatedData=True)
    assert token is None
    assert list(gen) == []

    gp.session.get.return_value = make_response({"nextPageToken": "only-token"})
    gen, token = CoreAlbum.list(gp)
    assert token == "only-token"
    assert list(gen) == []

    err = make_response({})
    err.raise_for_status.side_effect = HTTPError("nope")
    gp.session.get.return_value = err
    with pytest.raises(HTTPError):
        CoreAlbum.list(gp)


def test_album_from_core_create_get_from_dict(gp) -> None:
    gp.session.post.return_value = make_response(ALBUM_DICT)
    created = Album.create(gp, "Test Album")
    assert isinstance(created, Album)
    assert created.title == "Test Album"

    gp.session.get.return_value = make_response(ALBUM_DICT)
    got = Album.get(gp, "album-1")
    assert isinstance(got, Album) and got.id == "album-1"

    gp.session.get.return_value = make_response({}, status_code=400)
    assert Album.get(gp, "nope") is None

    from_dict = Album.from_dict(gp, ALBUM_DICT)
    assert from_dict.coverPhotoBaseUrl.startswith("https://")
    missing_covers = {
        "id": "a2",
        "title": "t",
        "productUrl": "u",
        "isWriteable": False,
    }
    stripped = Album.from_dict(gp, missing_covers)
    assert stripped.coverPhotoBaseUrl == ""
    assert stripped.coverPhotoMediaItemId == ""
    assert stripped.mediaItemsCount == 0


def test_all_albums_paginates(gp) -> None:
    pages = [
        make_response({"albums": [ALBUM_DICT], "nextPageToken": "n1"}),
        make_response({"albums": [ALBUM_DICT_MINIMAL]}),
    ]
    gp.session.get.side_effect = pages
    result = list(Album.all_albums(gp, pageSize=20))
    assert [a.id for a in result] == ["album-1", "album-min"]
    assert all(isinstance(a, Album) for a in result)


def test_all_albums_empty_then_token_without_albums(gp) -> None:
    gp.session.get.side_effect = [
        make_response({"nextPageToken": "n1"}),
        make_response({}),
    ]
    assert list(Album.all_albums(gp)) == []


def test_exists_by_id_name_and_errors(gp) -> None:
    gp.session.get.return_value = make_response(ALBUM_DICT)
    found = Album.exists(gp, id="album-1")
    assert found is not None and found.id == "album-1"

    gp.session.get.return_value = make_response({}, status_code=400)
    assert Album.exists(gp, id="missing") is None

    gp.session.get.side_effect = [
        make_response({"albums": [ALBUM_DICT]}),
    ]
    by_name = Album.exists(gp, name="Test Album")
    assert by_name is not None and by_name.title == "Test Album"

    gp.session.get.side_effect = [make_response({"albums": [ALBUM_DICT]})]
    assert Album.exists(gp, name="Other") is None

    gp.session.get.side_effect = None
    gp.session.get.return_value = make_response({})
    assert Album.exists(gp) is None  # neither id nor name: scan then None

    with pytest.raises(ValueError, match="only one"):
        Album.exists(gp, name="x", id="y")


def test_add_text_chunking_and_limit(gp) -> None:
    album = _album(gp)
    gp.session.post.return_value = make_response(
        {"enrichmentItem": {"id": "e1"}}
    )
    items = list(album.add_text(["Hello ", "world"]))
    assert items and items[0][1].id == "e1"

    with pytest.raises(ValueError, match="1000"):
        album.add_text(["x" * 1001])

    # exactly 1000 is allowed by HARD_LIMIT but triggers empty chunk + real chunk
    gp.session.post.return_value = make_response(
        {"enrichmentItem": {"id": "e2"}}
    )
    items = list(album.add_text(["y" * 1000]))
    assert len(items) >= 1

    # two parts that together exceed 1000 → multiple chunks (reversed)
    gp.session.post.return_value = make_response(
        {"enrichmentItem": {"id": "e3"}}
    )
    items = list(album.add_text(["a" * 600, "b" * 600]))
    assert len(items) == 2


def test_get_media_variants(gp) -> None:
    album = _album(gp)
    gp.session.post.return_value = make_response({}, status_code=500)
    assert list(album.get_media()) == []

    gp.session.post.return_value = make_response({"not": "items"}, status_code=200)
    assert list(album.get_media()) == []

    gp.session.post.return_value = make_response(
        {"mediaItems": [MEDIA_ITEM_DICT]}, status_code=200
    )
    media = list(album.get_media())
    assert len(media) == 1
    assert media[0].id == "media-1"


def test_set_title_updates_on_200(gp) -> None:
    album = _album(gp)
    gp.session.patch.return_value = make_response({}, status_code=200)
    resp = album.set_title("Renamed")
    assert resp.status_code == 200
    assert album.title == "Renamed"

    gp.session.patch.return_value = make_response({}, status_code=400)
    album.set_title("Nope")
    assert album.title == "Renamed"


def test_upload_and_add(gp, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    album = _album(gp)
    paths = []
    for i in range(2):
        p = tmp_path / f"f{i}.jpg"
        p.write_bytes(b"img")
        paths.append(str(p))

    monkeypatch.setattr(
        MediaItem,
        "upload_media",
        staticmethod(lambda gp, path, **kwargs: f"tok-{path}"),
    )

    fake_result = MediaItemResult(uploadToken="t")
    monkeypatch.setattr(
        MediaItem,
        "batchCreate",
        staticmethod(lambda gp, batch, albumId=None, albumPosition=None: [fake_result] * len(list(batch))),
    )
    results = album.upload_and_add(paths)
    assert len(results) == 2

    # force more than one batch (50+ items)
    many = [str(tmp_path / "x.jpg")] * 51
    (tmp_path / "x.jpg").write_bytes(b"x")
    results = album.upload_and_add(many)
    assert len(results) == 51
