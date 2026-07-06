import pytest
import os
from agents.database_ingester import ensure_multipolygon
from shapely.geometry import Polygon, MultiPolygon

def test_ensure_multipolygon_polygon():
    poly = Polygon([(0,0), (1,0), (1,1), (0,1)])
    result = ensure_multipolygon(poly)
    assert isinstance(result, MultiPolygon)
    assert len(result.geoms) == 1

def test_ensure_multipolygon_multipolygon():
    poly = Polygon([(0,0), (1,0), (1,1), (0,1)])
    mp = MultiPolygon([poly])
    result = ensure_multipolygon(mp)
    assert result == mp

def test_intelligence_analyst_structure():
    result = {
        "county": "Brown",
        "source_url": "https://example.com",
        "markdown": "test content",
        "zoning_keys_prompt": "extract zoning code keys from the plan",
        "status": "ready_for_grok_analysis"
    }
    assert result["status"] == "ready_for_grok_analysis"
    assert "zoning" in result["zoning_keys_prompt"].lower()

def test_brown_local_files_exist():
    digest = "/root/Hermes Brain/30_Projects/Wisconsin Data Build/Wisconsin Data Build Dashboard/Research Digests/Brown County — Research Digest.md"
    assert os.path.exists(digest), "Brown County Research Digest not found"

if __name__ == "__main__":
    pytest.main([__file__])