"""Public re-exports from gpsdk.__init__."""
from __future__ import annotations

from importlib.metadata import version

import gpsdk


def test_top_level_reexports() -> None:
    assert gpsdk.__version__ == version("google-photos-sdk")
    assert gpsdk.GooglePhotos is not None
    assert gpsdk.Album is not None
    assert gpsdk.MediaItem is not None
    assert gpsdk.CoreAlbum is not None
    assert gpsdk.CoreMediaItem is not None
    assert gpsdk.CoreEnrichmentItem is not None
    assert gpsdk.ProgressBar is not None
    assert gpsdk.RequestType is not None
    assert gpsdk.HeaderType is not None
    assert gpsdk.PositionType is not None
    assert gpsdk.EnrichmentType is not None
    assert gpsdk.SearchFilter is not None
    assert gpsdk.DateFilter is not None
    assert gpsdk.ContentFilter is not None
    assert gpsdk.MediaTypeFilter is not None
    assert gpsdk.FeatureFilter is not None
    assert gpsdk.SimpleMediaItem is not None
    assert gpsdk.NewMediaItem is not None
    assert gpsdk.AlbumPosition is not None
    assert gpsdk.Printable is not None
    assert gpsdk.Dictable is not None
    assert gpsdk.OnlyPrivate is not None
    assert gpsdk.IdEquality is not None
    assert gpsdk.SCOPES
    assert gpsdk.MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE == 25
    assert gpsdk.MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE == 100
    assert gpsdk.MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS == 50


def test_utils_package_reexports() -> None:
    from gpsdk import utils

    assert utils.get_python_version
    assert utils.split_iterable
    assert utils.batchify
    assert utils.ProgressBar
    assert utils.ProgressBarInjector
    assert utils.FileTime
    assert utils.FileTimeService
