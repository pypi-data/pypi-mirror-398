"""Tests for stock summary endpoint and models.

Note: The StockSummary model has been updated to match the actual API response.
Model parsing is tested in test_models_with_fixtures.py.
"""

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from gurufocus_api import (
    GeneralInfo,
    GuruFocusClient,
    InvalidSymbolError,
    QualityScores,
    RatioHistory,
    RatioIndustry,
    RatioValue,
    StockSummary,
    ValuationMetrics,
)

# Load sample response from fixtures
FIXTURES_DIR = Path(__file__).parent / "data"


def load_fixture() -> dict:
    """Load the FAKE1 summary fixture."""
    path = FIXTURES_DIR / "summary" / "FAKE1.json"
    with open(path) as f:
        return json.load(f)


SAMPLE_SUMMARY_RESPONSE = load_fixture()


class TestStockSummaryModel:
    """Tests for StockSummary Pydantic model."""

    def test_from_api_response_full(self) -> None:
        """Test parsing a complete API response."""
        summary = StockSummary.from_api_response(SAMPLE_SUMMARY_RESPONSE, "FAKE1")

        assert summary.symbol == "FAKE1"
        assert summary.general is not None
        assert summary.general.company_name == "Fake Company One"
        assert summary.general.sector == "TestSector"

    def test_general_info_parsed(self) -> None:
        """Test general info is correctly parsed."""
        summary = StockSummary.from_api_response(SAMPLE_SUMMARY_RESPONSE, "FAKE1")

        assert summary.general is not None
        assert isinstance(summary.general, GeneralInfo)
        assert summary.general.current_price is not None
        assert summary.general.current_price > 0

    def test_quality_scores_parsed(self) -> None:
        """Test quality scores are correctly parsed."""
        summary = StockSummary.from_api_response(SAMPLE_SUMMARY_RESPONSE, "FAKE1")

        assert summary.quality is not None
        assert isinstance(summary.quality, QualityScores)
        assert summary.quality.gf_score is not None
        assert 0 <= summary.quality.gf_score <= 100

    def test_valuation_metrics_parsed(self) -> None:
        """Test valuation metrics are correctly parsed."""
        summary = StockSummary.from_api_response(SAMPLE_SUMMARY_RESPONSE, "FAKE1")

        assert summary.valuation is not None
        assert isinstance(summary.valuation, ValuationMetrics)
        assert summary.valuation.gf_value is not None

    def test_from_api_response_minimal(self) -> None:
        """Test parsing a minimal API response."""
        minimal_response = {
            "summary": {
                "general": {
                    "company": "Test Company",
                }
            }
        }
        summary = StockSummary.from_api_response(minimal_response, "TEST")

        assert summary.symbol == "TEST"
        assert summary.general is not None
        assert summary.general.company_name == "Test Company"


class TestQualityScoresModel:
    """Tests for QualityScores model."""

    def test_quality_scores_with_all_fields(self) -> None:
        """Test QualityScores with all fields."""
        scores = QualityScores(
            gf_score=90,
            financial_strength=8,
            profitability_rank=9,
            growth_rank=7,
            gf_value_rank=6,
            momentum_rank=8,
        )
        assert scores.gf_score == 90
        assert scores.financial_strength == 8


class TestValuationMetricsModel:
    """Tests for ValuationMetrics model."""

    def test_valuation_metrics_all_fields(self) -> None:
        """Test ValuationMetrics with all fields."""
        valuation = ValuationMetrics(
            gf_value=200.0,
            graham_number=50.0,
            dcf_fcf_based=150.0,
        )
        assert valuation.gf_value == 200.0
        assert valuation.graham_number == 50.0


class TestRatioValueModel:
    """Tests for nested RatioValue model."""

    def test_ratio_value_nested_structure(self) -> None:
        """Test RatioValue with nested his and indu."""
        ratio = RatioValue(
            value=169.68,
            status=0,
            his=RatioHistory(low=36.87, high=175.46, med=110.57),
            indu=RatioIndustry(global_rank=17, indu_med=4.44, indu_tot=2399),
        )
        assert ratio.value == 169.68
        assert ratio.status == 0
        assert ratio.his is not None
        assert ratio.his.low == 36.87
        assert ratio.his.high == 175.46
        assert ratio.his.med == 110.57
        assert ratio.indu is not None
        assert ratio.indu.global_rank == 17
        assert ratio.indu.indu_med == 4.44
        assert ratio.indu.indu_tot == 2399

    def test_ratio_value_from_api_response(self) -> None:
        """Test RatioValue parsed from full API response."""
        summary = StockSummary.from_api_response(SAMPLE_SUMMARY_RESPONSE, "FAKE1")

        assert summary.ratios is not None
        assert summary.ratios.current_ratio is not None

        current_ratio = summary.ratios.current_ratio
        assert current_ratio.value == 1.32
        assert current_ratio.status == 1

        # Check nested history
        assert current_ratio.his is not None
        assert current_ratio.his.low == 0.60
        assert current_ratio.his.high == 1.80
        assert current_ratio.his.med == 1.20

        # Check nested industry
        assert current_ratio.indu is not None
        assert current_ratio.indu.global_rank == 1904
        assert current_ratio.indu.indu_med == 1.19
        assert current_ratio.indu.indu_tot == 2987

    def test_ratio_value_minimal(self) -> None:
        """Test RatioValue with only value."""
        ratio = RatioValue(value=50.0)
        assert ratio.value == 50.0
        assert ratio.his is None
        assert ratio.indu is None


class TestStocksEndpoint:
    """Tests for the stocks endpoint."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_summary_success(self) -> None:
        """Test successful get_summary call."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/FAKE1/summary").mock(
            return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE)
        )

        async with GuruFocusClient(api_token=api_token) as client:
            summary = await client.stocks.get_summary("FAKE1")

        assert isinstance(summary, StockSummary)
        assert summary.symbol == "FAKE1"
        assert summary.general is not None
        # Company name should be parsed from fixture
        assert summary.general.company_name is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_summary_lowercase_symbol(self) -> None:
        """Test that lowercase symbols are converted to uppercase."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/FAKE1/summary").mock(
            return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE)
        )

        async with GuruFocusClient(api_token=api_token) as client:
            summary = await client.stocks.get_summary("fake1")

        assert summary.symbol == "FAKE1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_summary_invalid_symbol(self) -> None:
        """Test get_summary with invalid symbol."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/INVALID/summary").mock(
            return_value=Response(404, text="Not found")
        )

        async with GuruFocusClient(api_token=api_token) as client:
            with pytest.raises(InvalidSymbolError) as exc_info:
                await client.stocks.get_summary("INVALID")
            assert exc_info.value.symbol == "INVALID"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_summary_raw(self) -> None:
        """Test get_summary_raw returns dict."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/FAKE1/summary").mock(
            return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE)
        )

        async with GuruFocusClient(api_token=api_token) as client:
            raw_data = await client.stocks.get_summary_raw("FAKE1")

        assert isinstance(raw_data, dict)
        assert "summary" in raw_data
