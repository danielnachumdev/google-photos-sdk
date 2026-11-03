"""Shared fixtures. Never touch real Google APIs or client_secrets.json."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from gpsdk.utils.pbar import DEFAULT_BAR_FORMAT, ProgressBar


class DummyProgressBar(ProgressBar):
    """Concrete ProgressBar for tests (also exercises ProgressBar.__init__)."""

    def __init__(
        self,
        total: Any = 0,
        position: int = 0,
        unit: str = "it",
        bar_format: str = DEFAULT_BAR_FORMAT,
        **kwargs: Any,
    ) -> None:
        super().__init__(total, position, unit, bar_format, **kwargs)
        self.updates: list = []
        self.writes: list = []
        self.reset_count = 0

    def update(self, amount: float = 1) -> None:
        self.updates.append(amount)

    def write(self, *args, sep=" ", end="\n") -> None:
        self.writes.append(sep.join(str(a) for a in args))

    def reset(self) -> None:
        self.reset_count += 1


ALBUM_DICT = {
    "id": "album-1",
    "title": "Test Album",
    "productUrl": "https://photos.example/album-1",
    "isWriteable": True,
    "mediaItemsCount": "3",
    "coverPhotoBaseUrl": "https://lh3.example/cover",
    "coverPhotoMediaItemId": "cover-1",
}

ALBUM_DICT_MINIMAL = {
    "id": "album-min",
    "title": "Minimal",
    "productUrl": "https://photos.example/album-min",
}

MEDIA_METADATA = {
    "creationTime": "2014-10-02T15:01:23Z",
    "width": "800",
    "height": "600",
    "photo": {"cameraMake": "Canon"},
}

MEDIA_ITEM_DICT = {
    "id": "media-1",
    "productUrl": "https://photos.example/media-1",
    "mimeType": "image/jpeg",
    "mediaMetadata": MEDIA_METADATA,
    "filename": "pic.jpg",
    "baseUrl": "https://lh3.example/media-1",
    "description": "a photo",
}

MEDIA_ITEM_DICT_MINIMAL = {
    "id": "media-min",
    "productUrl": "https://photos.example/media-min",
    "mimeType": "image/png",
    "mediaMetadata": {"creationTime": "2014-10-02T15:01:23Z"},
    "filename": "min.png",
}

MEDIA_ITEM_WITH_CONTRIBUTOR = {
    **MEDIA_ITEM_DICT,
    "id": "media-contrib",
    "ContributorInfo": {
        "profilePictureBaseUrl": "https://lh3.example/avatar",
        "displayName": "Ada",
    },
}


def make_response(
    json_data: Any = None,
    status_code: int = 200,
    content: bytes = b"",
    raise_exc: Exception | None = None,
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {} if json_data is None else json_data
    resp.content = content
    if raise_exc is not None:
        resp.raise_for_status.side_effect = raise_exc
    else:
        resp.raise_for_status.return_value = None
    return resp


@pytest.fixture(autouse=True)
def _disable_slowdown_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """upload_media is wrapped with @slowdown(2); never actually sleep."""
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)
    monkeypatch.setattr("gpsdk.utils.helpers.time.sleep", lambda *a, **k: None)


@pytest.fixture
def mock_credentials() -> MagicMock:
    creds = MagicMock()
    creds.token = "test-token"
    return creds


@pytest.fixture
def gp(monkeypatch: pytest.MonkeyPatch, mock_credentials: MagicMock):
    """GooglePhotos instance with OAuth and requests.Session fully mocked."""
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_credentials
    monkeypatch.setattr(
        "gpsdk.objects.core.gp.InstalledAppFlow.from_client_secrets_file",
        lambda *a, **k: mock_flow,
    )
    mock_session = MagicMock(name="Session")
    monkeypatch.setattr(
        "gpsdk.objects.core.gp.requests.Session",
        lambda: mock_session,
    )
    from gpsdk.objects.core.gp import GooglePhotos

    # Session() is mocked above, so __init__ already stores mock_session.
    return GooglePhotos(client_secrets_path="nonexistent_secrets.json")
