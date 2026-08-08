"""Tests for CoreMediaItem and MediaItem."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from requests import HTTPError

from gp_wrapper.objects.MediaItem import MediaItem
from gp_wrapper.objects.core.media_item.core_media_item import (
    MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS,
    MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE,
    CoreMediaItem,
)
from gp_wrapper.objects.core.media_item.filters import (
    ContentCategory,
    ContentFilter,
    Date,
    DateFilter,
    Feature,
    FeatureFilter,
    MediaType,
    MediaTypeFilter,
    SearchFilter,
)
from gp_wrapper.utils.structures.data_types import (
    AlbumPosition,
    MediaMetadata,
    NewMediaItem,
    SimpleMediaItem,
)
from gp_wrapper.utils.file_time import FileTime
from gp_wrapper.utils.structures.enums import MediaItemMaskTypes, PositionType

from .conftest import (
    DummyProgressBar,
    MEDIA_ITEM_DICT,
    MEDIA_ITEM_DICT_MINIMAL,
    MEDIA_ITEM_WITH_CONTRIBUTOR,
    make_response,
)


def _core(gp, dct=None) -> CoreMediaItem:
    return CoreMediaItem._from_dict(gp, dct or MEDIA_ITEM_DICT)


def test_from_dict_full_minimal_contributor_and_eq(gp) -> None:
    item = _core(gp)
    assert item.id == "media-1"
    assert item.description == "a photo"
    assert item.baseUrl.endswith("media-1")
    assert item.mediaMetadata.width == 800
    assert item.contributorInfo is None

    minimal = _core(gp, MEDIA_ITEM_DICT_MINIMAL)
    assert minimal.baseUrl is None
    assert minimal.description is None
    assert minimal.mediaMetadata.photo is None

    with_c = _core(gp, MEDIA_ITEM_WITH_CONTRIBUTOR)
    assert with_c.contributorInfo is not None
    assert with_c.contributorInfo.displayName == "Ada"

    assert item == _core(gp)
    assert item != minimal
    assert item != "media-1"
    assert hash(item) == hash("media-1")
    assert str(item)

    # mediaMetadata passed as object vs dict
    md = MediaMetadata.from_dict(MEDIA_ITEM_DICT["mediaMetadata"])
    direct = CoreMediaItem(
        gp,
        id="x",
        productUrl="u",
        mimeType="image/jpeg",
        mediaMetadata=md,
        filename="f.jpg",
    )
    assert direct.mediaMetadata is md
    via_dict = CoreMediaItem(
        gp,
        id="y",
        productUrl="u",
        mimeType="image/jpeg",
        mediaMetadata=MEDIA_ITEM_DICT["mediaMetadata"],
        filename="f.jpg",
    )
    assert via_dict.mediaMetadata.width == 800


def test_upload_media_image(gp, tmp_path) -> None:
    img = tmp_path / "pic.jpg"
    img.write_bytes(b"jpeg-bytes")
    gp.session.post.return_value = make_response(content=b"upload-token-1")
    token = CoreMediaItem.upload_media(gp, str(img))
    assert token == "upload-token-1"
    headers = gp.session.post.call_args.kwargs["headers"]
    assert headers["Content-Type"] == "application/json"
    assert "X-Goog-Upload-Protocol" in headers


def test_upload_media_mp4_octet(gp, tmp_path) -> None:
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"mp4-bytes")
    gp.session.post.return_value = make_response(content=b"tok-mp4")
    token = CoreMediaItem.upload_media(gp, str(video), pbar=DummyProgressBar(total=1))
    assert token == "tok-mp4"
    headers = gp.session.post.call_args.kwargs["headers"]
    assert headers["Content-Type"] == "application/octet-stream"
    assert headers["X-Goog-Upload-Content-Type"] == "video/mp4"


def test_upload_media_mov_converts_with_pbar(gp, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "clip.mov"
    src.write_bytes(b"mov-bytes")
    dest = tmp_path / "clip.mp4"

    mock_clip = MagicMock()

    def fake_write(path, **kwargs):
        dest.write_bytes(b"converted-mp4")

    mock_clip.write_videofile.side_effect = fake_write
    monkeypatch.setattr(
        "gp_wrapper.objects.core.media_item.core_media_item.moviepy.VideoFileClip",
        lambda path: mock_clip,
    )
    access = datetime(2015, 6, 15, 10, 0, 0)
    modification = datetime(2015, 6, 15, 18, 30, 0)
    creation = datetime(2026, 1, 1, 12, 0, 0)
    captured: dict = {}
    monkeypatch.setattr(
        "gp_wrapper.objects.core.media_item.core_media_item.FileTimeService.get",
        lambda self, path, follow_symlinks=True: FileTime(
            creation=creation, access=access, modification=modification
        ),
    )
    monkeypatch.setattr(
        "gp_wrapper.objects.core.media_item.core_media_item.FileTimeService.set",
        lambda self, path, ft, follow_symlinks=True: captured.update(path=path, ft=ft),
    )
    gp.session.post.return_value = make_response(content=b"tok-mov")
    bar = DummyProgressBar(total=1)
    token = CoreMediaItem.upload_media(gp, str(src), pbar=bar)
    assert token == "tok-mov"
    assert dest.exists()
    assert bar.writes  # conversion message
    mock_clip.write_videofile.assert_called()
    assert captured["path"] == str(dest)
    assert captured["ft"].access == access
    assert captured["ft"].modification == modification
    assert captured["ft"].creation is None


def test_upload_media_mov_copies_atime_mtime_to_converted_file(
    gp, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "clip.mov"
    dest = tmp_path / "clip.mp4"
    src.write_bytes(b"mov-bytes")
    dated = datetime(2015, 6, 15, 18, 30, 0)
    os.utime(src, (dated.timestamp(), dated.timestamp()))

    mock_clip = MagicMock()

    def fake_write(path, **kwargs):
        Path(path).write_bytes(b"converted-mp4")

    mock_clip.write_videofile.side_effect = fake_write
    monkeypatch.setattr(
        "gp_wrapper.objects.core.media_item.core_media_item.moviepy.VideoFileClip",
        lambda path: mock_clip,
    )
    gp.session.post.return_value = make_response(content=b"tok-dated")
    token = CoreMediaItem.upload_media(gp, str(src), pbar=DummyProgressBar(total=1))
    assert token == "tok-dated"
    st = os.stat(dest)
    assert abs(st.st_atime - dated.timestamp()) <= 2
    assert abs(st.st_mtime - dated.timestamp()) <= 2


def test_upload_media_mov_converts_without_pbar(
    gp, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """nachum_migrator calls upload_media(gp, path) with no pbar."""
    src = tmp_path / "clip.wmv"
    dest = tmp_path / "clip.mp4"
    src.write_bytes(b"wmv-bytes")
    dated = datetime(2015, 6, 15, 18, 30, 0)
    os.utime(src, (dated.timestamp(), dated.timestamp()))

    mock_clip = MagicMock()

    def fake_write(path, **kwargs):
        Path(path).write_bytes(b"converted-mp4")

    mock_clip.write_videofile.side_effect = fake_write
    monkeypatch.setattr(
        "gp_wrapper.objects.core.media_item.core_media_item.moviepy.VideoFileClip",
        lambda path: mock_clip,
    )
    gp.session.post.return_value = make_response(content=b"tok-no-pbar")
    token = CoreMediaItem.upload_media(gp, str(src), pbar=None)
    assert token == "tok-no-pbar"
    assert dest.exists()
    mock_clip.write_videofile.assert_called_once()
    st = os.stat(dest)
    assert abs(st.st_atime - dated.timestamp()) <= 2
    assert abs(st.st_mtime - dated.timestamp()) <= 2


def test_upload_media_mov_already_converted(gp, tmp_path) -> None:
    src = tmp_path / "clip.mov"
    src.write_bytes(b"mov")
    (tmp_path / "clip.mp4").write_bytes(b"already-mp4")
    gp.session.post.return_value = make_response(content=b"tok-existing")
    token = CoreMediaItem.upload_media(gp, str(src))
    assert token == "tok-existing"


def test_upload_media_http_error(gp, tmp_path) -> None:
    img = tmp_path / "pic.jpg"
    img.write_bytes(b"x")
    err = make_response(status_code=500)
    err.raise_for_status.side_effect = HTTPError("fail")
    gp.session.post.return_value = err
    with pytest.raises(HTTPError):
        CoreMediaItem.upload_media(gp, str(img))


def test_batch_create_validation_and_success(gp) -> None:
    with pytest.raises(ValueError, match="maximum"):
        CoreMediaItem.batchCreate(
            gp, [NewMediaItem("", SimpleMediaItem(f"t{i}")) for i in range(51)]
        )
    with pytest.raises(ValueError, match="albumPosition"):
        CoreMediaItem.batchCreate(
            gp,
            [NewMediaItem("", SimpleMediaItem("t"))],
            albumPosition=AlbumPosition(PositionType.LAST_IN_ALBUM),
        )

    gp.session.post.return_value = make_response(
        {
            "newMediaItemResults": [
                {"mediaItem": MEDIA_ITEM_DICT, "uploadToken": "t1", "gp": gp},
                {"status": {"message": "err", "code": 3}, "uploadToken": "t2"},
            ]
        }
    )
    # from_dict expects gp inside each dct; CoreMediaItem.batchCreate injects dct["gp"]=gp
    results = CoreMediaItem.batchCreate(
        gp,
        [NewMediaItem("d", SimpleMediaItem("t1", "a.jpg"))],
        albumId="album-1",
        albumPosition=AlbumPosition(PositionType.LAST_IN_ALBUM),
    )
    assert len(results) == 2
    assert results[0].mediaItem is not None
    assert results[1].status is not None

    gp.session.post.return_value = make_response({"newMediaItemResults": []})
    assert CoreMediaItem.batchCreate(gp, []) == []


def test_batch_create_http_error(gp) -> None:
    err = make_response()
    err.raise_for_status.side_effect = HTTPError("x")
    gp.session.post.return_value = err
    with pytest.raises(HTTPError):
        CoreMediaItem.batchCreate(gp, [NewMediaItem("", SimpleMediaItem("t"))])


def test_batch_get_and_get(gp) -> None:
    gp.session.get.return_value = make_response(
        {
            "mediaItemResults": [
                {"mediaItem": MEDIA_ITEM_DICT},
                {"status": {"message": "missing"}},
            ]
        }
    )
    results = list(CoreMediaItem.batchGet(gp, ["media-1", "nope"]))
    assert results[0].mediaItem is not None
    assert results[1].status is not None

    gp.session.get.return_value = make_response(MEDIA_ITEM_DICT)
    resp = CoreMediaItem.get(gp, "media-1")
    assert resp.json()["id"] == "media-1"

    err = make_response()
    err.raise_for_status.side_effect = HTTPError("x")
    gp.session.get.return_value = err
    with pytest.raises(HTTPError):
        CoreMediaItem.get(gp, "bad")
    with pytest.raises(HTTPError):
        list(CoreMediaItem.batchGet(gp, ["bad"]))


def test_search_validation_and_filters(gp) -> None:
    filters = SearchFilter(
        dateFilter=DateFilter(dates=[Date(2020, 1, 1)]),
        contentFilter=ContentFilter(includedContentCategories=[ContentCategory.FOOD]),
        featureFilter=FeatureFilter([Feature.FAVORITES]),
        mediaTypeFilter=MediaTypeFilter([MediaType.PHOTO]),
    )
    with pytest.raises(ValueError, match="conjunction"):
        CoreMediaItem.search(gp, albumId="a1", filters=filters)
    with pytest.raises(ValueError, match="pageSize"):
        CoreMediaItem.search(gp, pageSize=0)
    with pytest.raises(ValueError, match="pageSize"):
        CoreMediaItem.search(gp, pageSize=101)
    with pytest.raises(ValueError, match="orderBy"):
        CoreMediaItem.search(gp, orderBy="MediaMetadata.creation_time")

    gp.session.post.return_value = make_response(
        {"mediaItems": [MEDIA_ITEM_DICT], "nextPageToken": "n1"}
    )
    gen, token = CoreMediaItem.search(
        gp,
        pageSize=10,
        pageToken="prev",
        filters=filters,
        orderBy="MediaMetadata.creation_time desc",
    )
    assert token == "n1"
    items = list(gen)
    assert items[0].id == "media-1"
    payload = gp.session.post.call_args.kwargs["json"]
    assert "filters" in payload
    assert payload["pageToken"] == "prev"
    assert "contentFilter" in payload["filters"]
    assert "dateFilter" in payload["filters"]
    assert "featureFilter" in payload["filters"]
    assert "mediaTypeFilter" in payload["filters"]

    gp.session.post.return_value = make_response({"mediaItems": [MEDIA_ITEM_DICT]})
    gen, token = CoreMediaItem.search(gp, albumId="album-1")
    assert token is None
    assert list(gen)[0].id == "media-1"

    gp.session.post.return_value = make_response({})
    gen, token = CoreMediaItem.search(gp)
    assert token is None
    assert list(gen) == []

    err = make_response()
    err.raise_for_status.side_effect = HTTPError("x")
    gp.session.post.return_value = err
    with pytest.raises(HTTPError):
        CoreMediaItem.search(gp)


def test_list_validation_and_pages(gp) -> None:
    with pytest.raises(ValueError, match="pageSize"):
        CoreMediaItem.list(gp, pageSize=0)
    with pytest.raises(ValueError, match="pageSize"):
        CoreMediaItem.list(gp, pageSize=MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE + 1)

    gp.session.get.return_value = make_response(
        {"mediaItems": [MEDIA_ITEM_DICT], "nextPageToken": "t2"}
    )
    items, token = CoreMediaItem.list(gp, pageSize=10, pageToken="t1")
    assert token == "t2"
    assert items[0].id == "media-1"

    gp.session.get.return_value = make_response({})
    items, token = CoreMediaItem.list(gp)
    assert items == [] and token is None

    err = make_response()
    err.raise_for_status.side_effect = HTTPError("x")
    gp.session.get.return_value = err
    with pytest.raises(HTTPError):
        CoreMediaItem.list(gp)


def test_patch(gp) -> None:
    item = _core(gp)
    gp.session.patch.return_value = make_response({})
    resp = item.patch(MediaItemMaskTypes.DESCRIPTION, "new desc")
    assert resp.status_code == 200
    err = make_response()
    err.raise_for_status.side_effect = HTTPError("x")
    gp.session.patch.return_value = err
    with pytest.raises(HTTPError):
        item.patch(MediaItemMaskTypes.DESCRIPTION, "x")


def test_media_item_from_dict_and_from_core(gp) -> None:
    mi = MediaItem.from_dict(gp, MEDIA_ITEM_DICT)
    assert isinstance(mi, MediaItem)
    assert mi.id == "media-1"
    core = _core(gp)
    wrapped = MediaItem._from_core(core)
    assert wrapped.filename == core.filename


def test_media_item_list_and_batch_create_delegate(gp) -> None:
    gp.session.get.return_value = make_response({"mediaItems": [MEDIA_ITEM_DICT]})
    items, token = MediaItem.list(gp)
    assert isinstance(items[0], MediaItem)
    assert token is None

    gp.session.post.return_value = make_response(
        {"newMediaItemResults": [{"mediaItem": MEDIA_ITEM_DICT}]}
    )
    results = MediaItem.batchCreate(gp, [NewMediaItem("", SimpleMediaItem("t"))])
    assert results[0].mediaItem is not None


def test_search_all_tokens_and_validation(gp) -> None:
    with pytest.raises(ValueError, match="positive"):
        list(MediaItem.search_all(gp, tokens_to_use=0))
    with pytest.raises(ValueError, match="positive"):
        list(MediaItem.search_all(gp, tokens_to_use=-1))

    gp.session.post.side_effect = [
        make_response({"mediaItems": [MEDIA_ITEM_DICT], "nextPageToken": "n1"}),
        make_response({"mediaItems": [MEDIA_ITEM_DICT_MINIMAL]}),
    ]
    found = list(MediaItem.search_all(gp, pageSize=25, tokens_to_use=2))
    assert [m.id for m in found] == ["media-1", "media-min"]
    assert all(isinstance(m, MediaItem) for m in found)

    gp.session.post.side_effect = [
        make_response({"mediaItems": [MEDIA_ITEM_DICT], "nextPageToken": "n1"}),
        make_response({"mediaItems": [MEDIA_ITEM_DICT_MINIMAL]}),
    ]
    # only one token: do not follow next page
    found = list(MediaItem.search_all(gp, tokens_to_use=1))
    assert [m.id for m in found] == ["media-1"]

    gp.session.post.side_effect = None
    gp.session.post.return_value = make_response(
        {"mediaItems": [MEDIA_ITEM_DICT], "nextPageToken": "n1"}
    )
    found = list(
        MediaItem.search_all(
            gp,
            albumId="album-1",
            filters=None,
            orderBy=None,
            tokens_to_use=1,
        )
    )
    assert found[0].id == "media-1"


def test_all_media(gp) -> None:
    gp.session.get.side_effect = [
        make_response({"mediaItems": [MEDIA_ITEM_DICT], "nextPageToken": "n1"}),
        make_response({"mediaItems": [MEDIA_ITEM_DICT_MINIMAL]}),
    ]
    found = list(MediaItem.all_media(gp))
    assert [m.id for m in found] == ["media-1", "media-min"]


def test_add_to_library(gp, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = []
    for i in range(2):
        p = tmp_path / f"p{i}.jpg"
        p.write_bytes(b"img")
        paths.append(str(p))

    monkeypatch.setattr(
        MediaItem,
        "upload_media",
        staticmethod(lambda gp, path: f"tok-{path}"),
    )

    class FakeResult:
        def __init__(self, media_item):
            self.mediaItem = media_item

    fake_mi = MagicMock()
    monkeypatch.setattr(
        MediaItem,
        "batchCreate",
        staticmethod(lambda gp, batch, albumId=None, albumPosition=None: [
            FakeResult(fake_mi) for _ in batch
        ]),
    )
    result = MediaItem.add_to_library(gp, paths)
    assert result == [fake_mi, fake_mi]

    many = [str(tmp_path / "z.jpg")] * (MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS + 1)
    (tmp_path / "z.jpg").write_bytes(b"z")
    result = MediaItem.add_to_library(gp, many)
    assert len(result) == MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS + 1


def test_set_description(gp) -> None:
    mi = MediaItem.from_dict(gp, MEDIA_ITEM_DICT)
    gp.session.patch.return_value = make_response({}, status_code=200)
    resp = mi.set_description("updated")
    assert resp.status_code == 200
    assert mi.description == "updated"

    gp.session.patch.return_value = make_response({}, status_code=400)
    # patch() calls raise_for_status; make it a no-op so we can hit the != 200 branch
    gp.session.patch.return_value.raise_for_status.return_value = None
    mi.set_description("ignored")
    assert mi.description == "updated"
