"""Tests for GooglePhotos (OAuth + request layer fully mocked)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gp_wrapper.objects.core.gp import GooglePhotos
from gp_wrapper.utils.pbar import ProgressBarInjector
from gp_wrapper.utils.structures.enums import HeaderType, RequestType

from .conftest import DummyProgressBar, MEDIA_ITEM_DICT, make_response


def test_init_uses_installed_app_flow(gp) -> None:
    assert gp.credentials.token == "test-token"
    assert gp.session is not None


def test_init_does_not_read_real_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    def fake_from_file(path, scopes):
        seen["path"] = path
        seen["scopes"] = scopes
        flow = MagicMock()
        flow.run_local_server.return_value = MagicMock(token="abc")
        return flow

    monkeypatch.setattr(
        "gp_wrapper.objects.core.gp.InstalledAppFlow.from_client_secrets_file",
        fake_from_file,
    )
    monkeypatch.setattr(
        "gp_wrapper.objects.core.gp.requests.Session",
        lambda: MagicMock(),
    )
    GooglePhotos(client_secrets_path="not-a-real-file.json")
    assert seen["path"] == "not-a-real-file.json"
    assert seen["scopes"]


def test_only_private_blocks_external_assignment(gp) -> None:
    with pytest.raises(AttributeError, match="private"):
        gp.credentials = None  # type: ignore[misc]


def test_request_json_get_post_patch(gp) -> None:
    gp.session.get.return_value = make_response({"ok": True})
    gp.session.post.return_value = make_response({"ok": True})
    gp.session.patch.return_value = make_response({"ok": True})

    r1 = gp.request(RequestType.GET, "https://example.com/get")
    assert r1.json() == {"ok": True}
    get_kwargs = gp.session.get.call_args.kwargs
    assert get_kwargs["headers"]["Authorization"] == "Bearer test-token"
    assert get_kwargs["headers"]["Content-Type"] == "application/json"

    gp.request(
        RequestType.POST,
        "https://example.com/post",
        header_type=HeaderType.DEFAULT,
        additional_headers={"X-Custom": "1"},
        json={"a": 1},
    )
    post_headers = gp.session.post.call_args.kwargs["headers"]
    assert "Content-Type" not in post_headers
    assert post_headers["X-Custom"] == "1"

    gp.request(RequestType.PATCH, "https://example.com/patch", json={"b": 2})
    gp.session.patch.assert_called_once()


def test_request_with_progress_bar_wraps_data(gp) -> None:
    gp.session.post.return_value = make_response(content=b"tok")
    bar = DummyProgressBar(total=1)
    gp.request(
        RequestType.POST,
        "https://example.com/upload",
        header_type=HeaderType.OCTET,
        pbar=bar,
        data=b"payload-bytes",
    )
    data = gp.session.post.call_args.kwargs["data"]
    assert isinstance(data, ProgressBarInjector)
    assert gp.session.post.call_args.kwargs["headers"]["Content-Type"] == "application/octet-stream"


def test_get_media_item_id_success(gp) -> None:
    gp.session.post.return_value = make_response(
        {"newMediaItemResults": [{"mediaItem": MEDIA_ITEM_DICT}]}
    )
    item = gp._get_media_item_id("upload-token")
    assert item.id == "media-1"
    assert item.filename == "pic.jpg"


def test_get_media_item_id_missing_results(gp, capsys) -> None:
    gp.session.post.return_value = make_response({"error": "nope"})
    with pytest.raises(AttributeError, match="newMediaItemResults"):
        gp._get_media_item_id("upload-token")
    captured = capsys.readouterr()
    assert "nope" in captured.out or "error" in captured.out


def test_google_photos_str(gp) -> None:
    text = str(gp)
    assert "{" in text
