"""Tests for the search_guidelines function."""

import pytest

from guidelinely import GuidelineSearchResult, search_guidelines
from guidelinely.exceptions import GuidelinelyAPIError

API_BASE = "https://guidelines.1681248.com/api/v1"


class TestSearchGuidelines:
    """Tests for search_guidelines function."""

    def test_search_by_parameter(self, httpx_mock):
        """Test searching guidelines by parameter name."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?parameter=aluminum&limit=100",
            json=[
                {
                    "id": 123,
                    "parameter": "Aluminum",
                    "parameter_specification": "Aluminum, Dissolved",
                    "receptor": "Aquatic Life",
                    "media": "Surface Water",
                    "purpose": "Protection",
                    "table": "Table 2",
                    "table_name": "Chronic Aquatic Life Guidelines",
                    "source_abbreviation": "AEPA",
                    "document_abbreviation": "PAL",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(parameter="aluminum")

        assert len(results) == 1
        assert isinstance(results[0], GuidelineSearchResult)
        assert results[0].parameter == "Aluminum"
        assert results[0].table_name == "Chronic Aquatic Life Guidelines"
        assert results[0].source_abbreviation == "AEPA"

    def test_search_by_media_and_receptor(self, httpx_mock):
        """Test searching guidelines by media and receptor."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?receptor=aquatic_life&media=surface_water&limit=100",
            json=[
                {
                    "id": 124,
                    "parameter": "Copper",
                    "receptor": "Aquatic Life",
                    "media": "Surface Water",
                },
                {
                    "id": 125,
                    "parameter": "Zinc",
                    "receptor": "Aquatic Life",
                    "media": "Surface Water",
                },
            ],
            status_code=200,
        )

        results = search_guidelines(media="surface_water", receptor="aquatic_life")

        assert len(results) == 2
        assert results[0].parameter == "Copper"
        assert results[1].parameter == "Zinc"

    def test_search_by_source_abbreviation(self, httpx_mock):
        """Test searching guidelines by source abbreviation."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?source_abbreviation=CCME&limit=100",
            json=[
                {
                    "id": 200,
                    "parameter": "Lead",
                    "source_abbreviation": "CCME",
                    "source": "Canadian Council of Ministers",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(source_abbreviation="CCME")

        assert len(results) == 1
        assert results[0].source_abbreviation == "CCME"

    def test_search_with_limit(self, httpx_mock):
        """Test searching guidelines with custom limit."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?parameter=copper&limit=10",
            json=[{"id": i, "parameter": "Copper"} for i in range(10)],
            status_code=200,
        )

        results = search_guidelines(parameter="copper", limit=10)

        assert len(results) == 10

    def test_search_by_season(self, httpx_mock):
        """Test searching guidelines by season."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?season=winter&limit=100",
            json=[
                {
                    "id": 300,
                    "parameter": "Dissolved Oxygen",
                    "season": "Winter",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(season="winter")

        assert len(results) == 1
        assert results[0].season == "Winter"

    def test_search_by_location(self, httpx_mock):
        """Test searching guidelines by location."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?location=alberta&limit=100",
            json=[
                {
                    "id": 400,
                    "parameter": "Arsenic",
                    "location": "Alberta",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(location="alberta")

        assert len(results) == 1
        assert results[0].location == "Alberta"

    def test_search_multiple_filters(self, httpx_mock):
        """Test searching guidelines with multiple filters."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?parameter=aluminum&media=groundwater&source_abbreviation=AEPA&purpose=protection&limit=100",
            json=[
                {
                    "id": 500,
                    "parameter": "Aluminum",
                    "media": "Groundwater",
                    "source_abbreviation": "AEPA",
                    "purpose": "Protection",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(
            parameter="aluminum",
            media="groundwater",
            source_abbreviation="AEPA",
            purpose="protection",
        )

        assert len(results) == 1
        assert results[0].parameter == "Aluminum"
        assert results[0].media == "Groundwater"

    def test_search_empty_results(self, httpx_mock):
        """Test searching guidelines with no matches."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?parameter=nonexistent&limit=100",
            json=[],
            status_code=200,
        )

        results = search_guidelines(parameter="nonexistent")

        assert len(results) == 0
        assert results == []

    def test_search_api_error(self, httpx_mock):
        """Test handling of API errors."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?parameter=test&limit=100",
            json={"detail": "Invalid field name"},
            status_code=400,
        )

        with pytest.raises(GuidelinelyAPIError) as exc_info:
            search_guidelines(parameter="test")

        assert exc_info.value.status_code == 400
        assert "Invalid field name" in str(exc_info.value)

    def test_search_by_document_abbreviation(self, httpx_mock):
        """Test searching guidelines by document abbreviation."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?document_abbreviation=PAL&limit=100",
            json=[
                {
                    "id": 600,
                    "parameter": "Mercury",
                    "document_abbreviation": "PAL",
                    "document": "Provincial Ambient Guidelines",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(document_abbreviation="PAL")

        assert len(results) == 1
        assert results[0].document_abbreviation == "PAL"

    def test_search_by_exposure_duration(self, httpx_mock):
        """Test searching guidelines by exposure duration."""
        httpx_mock.add_response(
            method="GET",
            url=f"{API_BASE}/guidelines/search?exposure_duration=chronic&limit=100",
            json=[
                {
                    "id": 700,
                    "parameter": "Cadmium",
                    "exposure_duration": "Chronic",
                }
            ],
            status_code=200,
        )

        results = search_guidelines(exposure_duration="chronic")

        assert len(results) == 1
        assert results[0].exposure_duration == "Chronic"
