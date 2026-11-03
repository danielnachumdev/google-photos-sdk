"""Tests for media item search filters."""
from __future__ import annotations

import pytest

from gpsdk.objects.core.media_item.filters import (
    ContentCategory,
    ContentFilter,
    Date,
    DateFilter,
    DateRange,
    Feature,
    FeatureFilter,
    MediaType,
    MediaTypeFilter,
    SearchFilter,
)


def test_date_and_date_range_to_dict() -> None:
    d = Date(2020, 1, 2)
    assert d.to_dict() == {"year": 2020, "month": 1, "day": 2}
    rng = DateRange(Date(2020, 1, 1), Date(2020, 12, 31))
    assert rng.to_dict()["startDate"]["year"] == 2020
    assert rng.to_dict()["endDate"]["month"] == 12


def test_date_filter_validation_and_to_dict() -> None:
    with pytest.raises(ValueError, match="at-least one"):
        DateFilter()
    with pytest.raises(ValueError, match="maximum of 5 dates"):
        DateFilter(dates=[Date(2020, 1, i) for i in range(1, 7)])
    with pytest.raises(ValueError, match="maximum of 5 dates ranges"):
        DateFilter(
            ranges=[
                DateRange(Date(2020, i, 1), Date(2020, i, 2)) for i in range(1, 7)
            ]
        )
    only_dates = DateFilter(dates=[Date(2021, 5, 6)])
    assert only_dates.to_dict()["dates"][0]["year"] == 2021
    only_ranges = DateFilter(ranges=[DateRange(Date(2021, 1, 1), Date(2021, 2, 1))])
    assert "ranges" in only_ranges.to_dict()
    both = DateFilter(
        dates=[Date(2019, 1, 1)],
        ranges=[DateRange(Date(2019, 2, 1), Date(2019, 3, 1))],
    )
    dumped = both.to_dict()
    assert "dates" in dumped and "ranges" in dumped
    text = str(both)
    assert "dates" in text and "ranges" in text


def test_content_filter_validation_and_to_dict() -> None:
    with pytest.raises(ValueError, match="at-least one"):
        ContentFilter()
    with pytest.raises(ValueError, match="maximum of 10 included"):
        ContentFilter(includedContentCategories=[ContentCategory.FOOD] * 10)
    with pytest.raises(ValueError, match="maximum of 10 excluded"):
        ContentFilter(excludedContentCategories=[ContentCategory.PETS] * 10)
    inc = ContentFilter(includedContentCategories=[ContentCategory.LANDSCAPES])
    assert inc.to_dict() == {"includedContentCategories": ["LANDSCAPES"]}
    exc = ContentFilter(excludedContentCategories=[ContentCategory.RECEIPTS])
    assert exc.to_dict() == {"excludedContentCategories": ["RECEIPTS"]}
    both = ContentFilter(
        includedContentCategories=[ContentCategory.SELFIES, ContentCategory.PEOPLE],
        excludedContentCategories=[ContentCategory.DOCUMENTS],
    )
    d = both.to_dict()
    assert d["includedContentCategories"] == ["SELFIES", "PEOPLE"]
    assert d["excludedContentCategories"] == ["DOCUMENTS"]
    assert ContentCategory.NONE.value == "NONE"
    assert ContentCategory.HOLIDAYS.value == "HOLIDAYS"


def test_media_type_filter() -> None:
    with pytest.raises(ValueError, match="only one media type"):
        MediaTypeFilter([])
    with pytest.raises(ValueError, match="only one media type"):
        MediaTypeFilter([MediaType.VIDEO, MediaType.PHOTO])
    f = MediaTypeFilter([MediaType.PHOTO])
    assert f.to_dict() == {"mediaTypes": ["PHOTO"]}
    assert MediaType.ALL_MEDIA.value == "ALL_MEDIA"


def test_feature_filter() -> None:
    f = FeatureFilter([Feature.FAVORITES])
    assert f.to_dict() == {"includedFeatures": ["FAVORITES"]}
    empty = FeatureFilter([])
    assert empty.to_dict() == {"includedFeatures": []}
    assert Feature.NONE.value == "NONE"


def test_search_filter_defaults_and_str() -> None:
    sf = SearchFilter()
    assert sf.dateFilter is None
    assert sf.contentFilter is None
    assert sf.mediaTypeFilter is None
    assert sf.featureFilter is None
    assert sf.includeArchivedMedia is False
    assert sf.excludeNonAppCreatedData is False
    filled = SearchFilter(
        dateFilter=DateFilter(dates=[Date(2020, 1, 1)]),
        contentFilter=ContentFilter(includedContentCategories=[ContentCategory.FOOD]),
        mediaTypeFilter=MediaTypeFilter([MediaType.VIDEO]),
        featureFilter=FeatureFilter([Feature.FAVORITES]),
        includeArchivedMedia=True,
        excludeNonAppCreatedData=True,
    )
    text = str(filled)
    assert "includeArchivedMedia" in text
    assert filled.includeArchivedMedia is True
