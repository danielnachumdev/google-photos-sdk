"""Tests for enums, data types, and parent classes."""
from __future__ import annotations

import inspect
import json
from io import StringIO
from types import FrameType

import pytest

from gpsdk.utils.structures.data_types import (
    ALBUMS_ENDPOINT,
    DEFAULT_NUM_WORKERS,
    EMPTY_PROMPT_MESSAGE,
    MEDIA_ITEMS_CREATE_ENDPOINT,
    SCOPES,
    UPLOAD_MEDIA_ITEM_ENDPOINT,
    AlbumPosition,
    ContributorInfo,
    MediaItemResult,
    MediaMetadata,
    NewMediaItem,
    SimpleMediaItem,
    Status,
)
from gpsdk.utils.structures.enums import (
    AlbumMaskType,
    EnrichmentType,
    HeaderType,
    MediaItemMaskTypes,
    MimeType,
    PositionType,
    RelativeItemType,
    RequestType,
    StatusCode,
)
from gpsdk.utils.structures.parent_classes import (
    Dictable,
    IdEquality,
    IndentedWriter2,
    OnlyPrivate,
    Printable,
)

from .conftest import MEDIA_ITEM_DICT


def test_enums_values() -> None:
    assert RequestType.GET.value == "get"
    assert RequestType.POST.value == "post"
    assert RequestType.PATCH.value == "patch"
    assert HeaderType.DEFAULT.value == ""
    assert HeaderType.JSON.value == "json"
    assert HeaderType.OCTET.value == "octet-stream"
    assert MimeType.PNG.value == "image/png"
    assert MimeType.JPEG.value == "image/jpeg"
    assert MimeType.MP4.value == "video/mp4"
    assert MimeType.MOV.value == "video/quicktime"
    assert MimeType.WMV.value == "x-ms-asf"
    assert PositionType.FIRST_IN_ALBUM.value == "FIRST_IN_ALBUM"
    assert EnrichmentType.TEXT_ENRICHMENT.value == "textEnrichment"
    assert MediaItemMaskTypes.DESCRIPTION.value == "description"
    assert AlbumMaskType.TITLE.value == "title"
    assert AlbumMaskType.COVER_PHOTOS_MEDIA_ITEM_ID.value == "coverPhotoMediaItemId"
    assert RelativeItemType.relativeMediaItemId.value == "relativeMediaItemId"
    assert StatusCode.OK.value == 0
    assert StatusCode.NOT_FOUND.value == 5


def test_constants() -> None:
    assert EMPTY_PROMPT_MESSAGE == ""
    assert DEFAULT_NUM_WORKERS == 2
    assert ALBUMS_ENDPOINT.endswith("/albums")
    assert UPLOAD_MEDIA_ITEM_ENDPOINT.endswith("/uploads")
    assert MEDIA_ITEMS_CREATE_ENDPOINT.endswith("batchCreate")
    assert any("photoslibrary" in s for s in SCOPES)


def test_simple_media_item_ok_and_from_dict() -> None:
    item = SimpleMediaItem("tok", "file.jpg")
    assert item.uploadToken == "tok"
    assert item.fileName == "file.jpg"
    d = item.to_dict()
    assert d["uploadToken"] == "tok"
    roundtrip = SimpleMediaItem.from_dict({"uploadToken": "t2", "fileName": "b.png"})
    assert roundtrip.fileName == "b.png"
    no_name = SimpleMediaItem.from_dict({"uploadToken": "t3"})
    assert no_name.fileName is None


def test_simple_media_item_filename_too_long() -> None:
    with pytest.raises(ValueError, match="255"):
        SimpleMediaItem("tok", "x" * 256)


def test_new_media_item_ok_and_from_dict() -> None:
    simple = SimpleMediaItem("tok", "a.jpg")
    item = NewMediaItem("hello", simple)
    assert item.description == "hello"
    assert item.simpleMediaItem is simple
    d = item.to_dict()
    assert d["description"] == "hello"
    assert d["simpleMediaItem"]["uploadToken"] == "tok"
    rebuilt = NewMediaItem.from_dict(
        {"description": "d", "simpleMediaItem": {"uploadToken": "u", "fileName": "f"}}
    )
    assert rebuilt.description == "d"
    empty = NewMediaItem("", simple)
    assert empty.description == ""


def test_new_media_item_description_too_long() -> None:
    with pytest.raises(ValueError, match="1000"):
        NewMediaItem("x" * 1001, SimpleMediaItem("t"))


def test_album_position_default_and_after_media() -> None:
    pos = AlbumPosition()
    assert pos.position == PositionType.FIRST_IN_ALBUM
    assert pos.relativeMediaItemId is None
    assert pos.relativeEnrichmentItemId is None
    after = AlbumPosition(
        PositionType.AFTER_MEDIA_ITEM, relativeMediaItemId="mid-1"
    )
    assert after.relativeMediaItemId == "mid-1"
    d = after.to_dict()
    assert d["relativeMediaItemId"] == "mid-1"
    rebuilt = AlbumPosition.from_dict(
        {"position": PositionType.LAST_IN_ALBUM, "relativeMediaItemId": "x"}
    )
    assert rebuilt.position == PositionType.LAST_IN_ALBUM
    AlbumPosition.from_dict({"position": PositionType.FIRST_IN_ALBUM})


def test_album_position_to_dict_is_json_serializable() -> None:
    last = AlbumPosition(PositionType.LAST_IN_ALBUM)
    dumped = last.to_dict()
    assert dumped["position"] == "LAST_IN_ALBUM"
    assert isinstance(dumped["position"], str)
    assert dumped["relativeMediaItemId"] is None
    assert dumped["relativeEnrichmentItemId"] is None

    after = AlbumPosition(
        PositionType.AFTER_MEDIA_ITEM, relativeMediaItemId="mid-1"
    )
    payload = after.to_dict()
    assert payload["position"] == "AFTER_MEDIA_ITEM"
    assert payload["relativeMediaItemId"] == "mid-1"
    roundtrip = json.loads(json.dumps(payload))
    assert roundtrip["position"] == "AFTER_MEDIA_ITEM"
    assert roundtrip["relativeMediaItemId"] == "mid-1"


def test_album_position_after_enrichment_raises_due_to_existing_bug() -> None:
    """relativeEnrichmentItemId alone currently always trips ValueError (source bug)."""
    with pytest.raises(ValueError, match="exactly one"):
        AlbumPosition(
            PositionType.AFTER_ENRICHMENT_ITEM, relativeEnrichmentItemId="e1"
        )


def test_album_position_requires_exactly_one_relative_id() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        AlbumPosition(PositionType.AFTER_MEDIA_ITEM)
    with pytest.raises(ValueError, match="exactly one"):
        AlbumPosition(
            PositionType.AFTER_MEDIA_ITEM,
            relativeMediaItemId="m",
            relativeEnrichmentItemId="e",
        )


def test_status_and_from_dict() -> None:
    st = Status("ok", StatusCode.OK, [{"k": 1}])
    assert st.message == "ok"
    assert st.code == StatusCode.OK
    assert st.details == [{"k": 1}]
    minimal = Status.from_dict({"message": "m"})
    assert minimal.code is None
    full = Status.from_dict({"message": "m", "code": 0, "details": []})
    assert full.code == 0


def test_media_metadata_photo_and_video() -> None:
    md = MediaMetadata.from_dict(
        {
            "creationTime": "2014-10-02T15:01:23Z",
            "width": "100",
            "height": "50",
            "photo": {"iso": 100},
        }
    )
    assert md.width == 100
    assert md.height == 50
    assert md.photo == {"iso": 100}
    assert md.video is None
    assert md.creationTime.year == 2014
    vid = MediaMetadata("2014-10-02T15:01:23Z", video={"fps": 24})
    assert vid.video == {"fps": 24}
    assert vid.width is None
    d = md.to_dict()
    assert "creationTime" in d


def test_contributor_info() -> None:
    info = ContributorInfo.from_dict(
        {"profilePictureBaseUrl": "https://a", "displayName": "Ada"}
    )
    assert info.profilePictureBaseUrl == "https://a"
    assert info.displayName == "Ada"
    assert info.to_dict()["displayName"] == "Ada"


def test_media_item_result_without_media(gp) -> None:
    res = MediaItemResult.from_dict({"status": {"message": "fail", "code": 3}})
    assert res.mediaItem is None
    assert res.status is not None
    assert res.uploadToken is None
    constructed = MediaItemResult(uploadToken="u")
    assert constructed.uploadToken == "u"


def test_media_item_result_with_media(gp) -> None:
    res = MediaItemResult.from_dict(
        {
            "gp": gp,
            "mediaItem": MEDIA_ITEM_DICT,
            "status": {"message": "OK", "code": 0},
            "uploadToken": "up-1",
        }
    )
    assert res.uploadToken == "up-1"
    assert res.mediaItem is not None
    assert res.mediaItem.id == "media-1"


def test_printable_str_nested() -> None:
    item = NewMediaItem("desc", SimpleMediaItem("tok", "a.jpg"))
    text = str(item)
    assert "{" in text
    assert "description" in text
    assert "simpleMediaItem" in text
    assert "tok" in text


def test_dictable_default_from_dict() -> None:
    class Point(Dictable):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    p = Point.from_dict({"x": 1, "y": 2})
    assert p.x == 1 and p.y == 2
    assert p.to_dict() == {"x": 1, "y": 2}


def test_id_equality_with_and_without_id() -> None:
    class Item(IdEquality):
        def __init__(self, id):  # noqa: A002
            self.id = id

    a, b, c = Item("1"), Item("1"), Item("2")
    assert a == b
    assert a != c
    assert a != "1"
    assert hash(a) == hash("1")

    class NoId(IdEquality):
        pass

    x, y = NoId(), NoId()
    assert x != y
    assert x != x  # no id → always False
    assert isinstance(hash(x), int)


def test_only_private_allows_internal_setattr_blocks_external() -> None:
    class Box(OnlyPrivate):
        def __init__(self) -> None:
            self.value = 1

        def set_value(self, v: int) -> None:
            self.value = v

    box = Box()
    assert box.value == 1
    box.set_value(2)
    assert box.value == 2
    with pytest.raises(AttributeError, match="private"):
        box.value = 3


def test_only_private_caller_name_validation() -> None:
    with pytest.raises(TypeError, match="steps_back must be an int"):
        OnlyPrivate._OnlyPrivate__get_caller_name("x")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative"):
        OnlyPrivate._OnlyPrivate__get_caller_name(-1)
    name = OnlyPrivate._OnlyPrivate__get_caller_name(0)
    assert name is None or isinstance(name, str)
    assert OnlyPrivate._OnlyPrivate__get_caller_name(steps_back=5000) is None


def test_only_private_prev_frame_and_none_currentframe(monkeypatch: pytest.MonkeyPatch) -> None:
    assert OnlyPrivate._OnlyPrivate__get_prev_frame(None) is None
    assert OnlyPrivate._OnlyPrivate__get_prev_frame("not-a-frame") is None  # type: ignore[arg-type]
    frame = inspect.currentframe()
    assert isinstance(frame, FrameType)
    prev = OnlyPrivate._OnlyPrivate__get_prev_frame(frame)
    assert prev is None or isinstance(prev, FrameType)

    monkeypatch.setattr(inspect, "currentframe", lambda: None)
    assert OnlyPrivate._OnlyPrivate__get_caller_name() is None


def test_indented_writer_stream_add_from_undent() -> None:
    w = IndentedWriter2(indent_value="  ")
    w.write("root")
    w.indent()
    w.write("child")
    w.add_from("single")
    w.add_from("line1\nline2\nline3")
    w.undent()
    w.undent()
    assert w.indent_level == 0
    buf = StringIO()
    w.to_stream(buf)
    out = buf.getvalue()
    assert "root" in out
    assert "child" in out
    assert "line2" in out


def test_printable_is_used_by_search_filter_str() -> None:
    class Tiny(Printable):
        def __init__(self) -> None:
            self.flag = True

    assert '"flag"' in str(Tiny())
