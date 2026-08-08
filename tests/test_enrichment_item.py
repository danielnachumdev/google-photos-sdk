"""Tests for CoreEnrichmentItem."""
from __future__ import annotations

from gp_wrapper.objects.core.enrichment_item import CoreEnrichmentItem


def test_enrichment_item_id_and_str() -> None:
    item = CoreEnrichmentItem("enr-1")
    assert item.id == "enr-1"
    text = str(item)
    assert "CoreEnrichmentItem" in text
    assert "enr-1" in text
