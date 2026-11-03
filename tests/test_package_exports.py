"""Public re-exports from gp_wrapper.__init__."""
from __future__ import annotations

from importlib.metadata import version

import gp_wrapper


def test_top_level_reexports() -> None:
    assert gp_wrapper.__version__ == version("google-photos-sdk")
    assert gp_wrapper.GooglePhotos is not None
    assert gp_wrapper.Album is not None
    assert gp_wrapper.MediaItem is not None
    assert gp_wrapper.CoreAlbum is not None
    assert gp_wrapper.CoreMediaItem is not None
    assert gp_wrapper.CoreEnrichmentItem is not None
    assert gp_wrapper.ProgressBar is not None
    assert gp_wrapper.RequestType is not None
    assert gp_wrapper.HeaderType is not None
    assert gp_wrapper.PositionType is not None
    assert gp_wrapper.EnrichmentType is not None
    assert gp_wrapper.SearchFilter is not None
    assert gp_wrapper.DateFilter is not None
    assert gp_wrapper.ContentFilter is not None
    assert gp_wrapper.MediaTypeFilter is not None
    assert gp_wrapper.FeatureFilter is not None
    assert gp_wrapper.SimpleMediaItem is not None
    assert gp_wrapper.NewMediaItem is not None
    assert gp_wrapper.AlbumPosition is not None
    assert gp_wrapper.Printable is not None
    assert gp_wrapper.Dictable is not None
    assert gp_wrapper.OnlyPrivate is not None
    assert gp_wrapper.IdEquality is not None
    assert gp_wrapper.SCOPES
    assert gp_wrapper.MEDIA_ITEM_LIST_DEFAULT_PAGE_SIZE == 25
    assert gp_wrapper.MEDIA_ITEM_LIST_MAXIMUM_PAGE_SIZE == 100
    assert gp_wrapper.MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS == 50


def test_utils_package_reexports() -> None:
    from gp_wrapper import utils

    assert utils.get_python_version
    assert utils.split_iterable
    assert utils.batchify
    assert utils.ProgressBar
    assert utils.ProgressBarInjector
    assert utils.FileTime
    assert utils.FileTimeService
