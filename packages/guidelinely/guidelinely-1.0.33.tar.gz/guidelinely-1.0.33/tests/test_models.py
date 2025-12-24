"""Tests for Pydantic data models."""

import pytest

from guidelinely.models import (
    BatchCalculateRequest,
    CalculateRequest,
    CalculationResponse,
    GuidelineResponse,
    ParameterWithUnit,
    SourceDocument,
    SourceResponse,
    StatsResponse,
)


def test_guideline_response_valid():
    """Test creating a valid GuidelineResponse."""
    data = {
        "id": 1,
        "parameter": "Aluminum",
        "parameter_specification": "Aluminum, Dissolved",
        "media": "surface_water",
        "value": "[87.0 μg/L,100 μg/L]",
        "lower": 87.0,
        "upper": 100.0,
        "unit": "μg/L",
        "is_calculated": True,
        "source": "CCME",
        "receptor": "Aquatic Life",
        "exposure_duration": "chronic",
        "purpose": "long_term",
        "table": "Table 1",
        "table_name": "Chronic Aquatic Life Guidelines",
        "application": "Freshwater guidelines",
        "basis": "Chronic toxicity",
        "use_case": "Protection",
        "document": "CCME Water Quality Guidelines",
    }

    guideline = GuidelineResponse(**data)
    assert guideline.parameter_specification == "Aluminum, Dissolved"
    assert guideline.table_name == "Chronic Aquatic Life Guidelines"
    assert guideline.lower == 87.0
    assert guideline.upper == 100.0


def test_guideline_response_optional_fields():
    """Test that optional fields can be None."""
    data = {
        "id": 1,
        "parameter": "Aluminum",
        "parameter_specification": "Aluminum, Dissolved",
        "media": "surface_water",
        "value": "[87.0 μg/L,100 μg/L]",
        "unit": "μg/L",
        "is_calculated": True,
        "source": "CCME",
        "receptor": "Aquatic Life",
        "exposure_duration": "chronic",
        "purpose": "long_term",
        "table": "Table 1",
        "table_name": "Chronic Aquatic Life Guidelines",
        "application": "Freshwater guidelines",
        "basis": "Chronic toxicity",
        "document": "CCME Water Quality Guidelines",
    }

    guideline = GuidelineResponse(**data)
    assert guideline.table_name == "Chronic Aquatic Life Guidelines"
    assert guideline.narrative is None
    assert guideline.lower is None
    assert guideline.upper is None
    assert guideline.use_case is None  # Should be None when not provided
    assert guideline.context_index is None


def test_calculation_response_valid():
    """Test creating a valid CalculationResponse."""
    data = {
        "results": [
            {
                "id": 1,
                "parameter": "Aluminum",
                "parameter_specification": "Aluminum, Dissolved",
                "media": "surface_water",
                "value": "[87.0 μg/L,100 μg/L]",
                "unit": "μg/L",
                "is_calculated": True,
                "source": "CCME",
                "receptor": "Aquatic Life",
                "exposure_duration": "chronic",
                "purpose": "long_term",
                "table": "Table 1",
                "table_name": "Chronic Aquatic Life Guidelines",
                "application": "Freshwater guidelines",
                "basis": "Chronic toxicity",
                "use_case": "Protection",
                "document": "CCME Water Quality Guidelines",
            }
        ],
        "context": {"pH": "7.0 1", "hardness": "100 mg/L"},
        "total_count": 1,
    }

    response = CalculationResponse(**data)
    assert len(response.results) == 1
    assert response.results[0].table_name == "Chronic Aquatic Life Guidelines"
    assert response.total_count == 1
    assert response.results[0].parameter_specification == "Aluminum, Dissolved"
    assert response.contexts is None  # Optional field


def test_calculate_request_valid():
    """Test creating a valid CalculateRequest."""
    request = CalculateRequest(
        parameter="Aluminum",
        media="surface_water",
        context={"pH": "7.0 1", "hardness": "100 mg/L"},
        target_unit="mg/L",
    )

    assert request.parameter == "Aluminum"
    assert request.media == "surface_water"
    assert request.context["pH"] == "7.0 1"


def test_calculate_request_minimal():
    """Test CalculateRequest with only required fields."""
    request = CalculateRequest(parameter="Aluminum", media="surface_water")

    assert request.parameter == "Aluminum"
    assert request.context is None
    assert request.target_unit is None


def test_batch_calculate_request_valid():
    """Test creating a valid BatchCalculateRequest."""
    request = BatchCalculateRequest(
        parameters=["Aluminum", "Copper", "Lead"], media="surface_water", context={"pH": "7.0 1"}
    )

    assert len(request.parameters) == 3
    assert request.media == "surface_water"


def test_batch_calculate_request_parameter_limit():
    """Test that parameter count validation enforces limit during instantiation."""
    params = ["Aluminum"] * 51

    with pytest.raises(ValueError, match="Maximum 50 parameters"):
        BatchCalculateRequest(parameters=params, media="surface_water")


def test_batch_calculate_request_mixed_parameters():
    """Test BatchCalculateRequest with mixed string and dict parameters."""
    request = BatchCalculateRequest(
        parameters=["Aluminum", {"name": "Copper", "target_unit": "μg/L"}], media="surface_water"
    )

    assert len(request.parameters) == 2
    assert request.parameters[0] == "Aluminum"
    assert isinstance(request.parameters[1], ParameterWithUnit)
    assert request.parameters[1].name == "Copper"
    assert request.parameters[1].target_unit == "μg/L"


def test_source_response_valid():
    """Test creating a valid SourceResponse with nested documents."""
    data = {
        "id": 1,
        "name": "Canadian Council of Ministers of the Environment",
        "abbreviation": "CCME",
        "documents": [
            {
                "id": 1,
                "name": "Canadian Water Quality Guidelines",
                "abbreviation": "CWQG",
                "url": "https://example.com",
            },
            {"id": 2, "name": "Canadian Soil Quality Guidelines", "abbreviation": "CSQG"},
        ],
    }

    source = SourceResponse(**data)
    assert source.id == 1
    assert source.name == "Canadian Council of Ministers of the Environment"
    assert source.abbreviation == "CCME"
    assert len(source.documents) == 2
    assert source.documents[0].name == "Canadian Water Quality Guidelines"
    assert source.documents[0].abbreviation == "CWQG"
    assert source.documents[0].url == "https://example.com"
    assert source.documents[1].url is None


def test_source_document_optional_fields():
    """Test SourceDocument with optional fields."""
    data = {"id": 1, "name": "Test Document"}
    doc = SourceDocument(**data)
    assert doc.id == 1
    assert doc.name == "Test Document"
    assert doc.abbreviation is None
    assert doc.url is None


def test_stats_response_valid():
    """Test creating a valid StatsResponse."""
    data = {
        "parameters": 150,
        "guidelines": 5000,
        "sources": 12,
        "documents": 45,
    }

    stats = StatsResponse(**data)
    assert stats.parameters == 150
    assert stats.guidelines == 5000
    assert stats.sources == 12
    assert stats.documents == 45
