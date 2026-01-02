"""Tests for insider activity endpoints.

Note: Model parsing with real API responses is tested in test_models_with_fixtures.py.
These tests focus on endpoint behavior.
"""

import json
import tempfile
from pathlib import Path

import pytest
import respx
from httpx import Response

from gurufocus_api import (
    ClusterBuyResponse,
    DoubleBuyResponse,
    GuruFocusClient,
    InsiderBuysResponse,
    InsiderListResponse,
    InsiderUpdatesResponse,
    TripleBuyResponse,
)

# Load sample responses from fixtures
FIXTURES_DIR = Path(__file__).parent / "data"


def load_fixture(category: str, name: str = "page1") -> dict | list:
    """Load a fixture file."""
    path = FIXTURES_DIR / category / f"{name}.json"
    with open(path) as f:
        return json.load(f)


SAMPLE_UPDATES_RESPONSE = load_fixture("insider_updates")
SAMPLE_CEO_BUYS_RESPONSE = load_fixture("insider_ceo_buys")
SAMPLE_CFO_BUYS_RESPONSE = load_fixture("insider_cfo_buys")
SAMPLE_CLUSTER_BUY_RESPONSE = load_fixture("insider_cluster_buy")
SAMPLE_DOUBLE_RESPONSE = load_fixture("insider_double")
SAMPLE_TRIPLE_RESPONSE = load_fixture("insider_triple")
SAMPLE_LIST_RESPONSE = load_fixture("insider_list")


class TestInsiderUpdatesEndpoint:
    """Tests for insider updates endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_updates(self, cache_dir: Path) -> None:
        """Test fetching insider updates returns typed model."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/insider_updates").mock(
            return_value=Response(200, json=SAMPLE_UPDATES_RESPONSE)
        )

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            updates = await client.insiders.get_updates()

            assert isinstance(updates, InsiderUpdatesResponse)
            assert len(updates.updates) == 3
            assert updates.updates[0].symbol == "NYSE:FAKE1"
            assert updates.updates[0].insider == "John Smith"
            assert updates.updates[0].type == "P"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_updates_cached(self, cache_dir: Path) -> None:
        """Test that updates are cached."""
        api_token = "test-token"
        route = respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_updates"
        ).mock(return_value=Response(200, json=SAMPLE_UPDATES_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            await client.insiders.get_updates()
            await client.insiders.get_updates()
            assert route.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_updates_raw(self, cache_dir: Path) -> None:
        """Test fetching raw updates data."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/insider_updates").mock(
            return_value=Response(200, json=SAMPLE_UPDATES_RESPONSE)
        )

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            raw = await client.insiders.get_updates_raw()
            assert isinstance(raw, list)
            assert len(raw) == 3


class TestInsiderCeoBuysEndpoint:
    """Tests for insider CEO buys endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_ceo_buys(self, cache_dir: Path) -> None:
        """Test fetching CEO buys returns typed model."""
        api_token = "test-token"
        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_ceo"
        ).mock(return_value=Response(200, json=SAMPLE_CEO_BUYS_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            ceo_buys = await client.insiders.get_ceo_buys()

            assert isinstance(ceo_buys, InsiderBuysResponse)
            assert ceo_buys.total == 500
            assert ceo_buys.current_page == 1
            assert len(ceo_buys.data) == 3
            assert ceo_buys.data[0].symbol == "FAKE1"
            assert ceo_buys.data[0].name == "John Smith"
            assert ceo_buys.data[0].position == "CEO"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_ceo_buys_cached(self, cache_dir: Path) -> None:
        """Test that CEO buys are cached."""
        api_token = "test-token"
        route = respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_ceo"
        ).mock(return_value=Response(200, json=SAMPLE_CEO_BUYS_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            await client.insiders.get_ceo_buys()
            await client.insiders.get_ceo_buys()
            assert route.call_count == 1


class TestInsiderCfoBuysEndpoint:
    """Tests for insider CFO buys endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_cfo_buys(self, cache_dir: Path) -> None:
        """Test fetching CFO buys returns typed model."""
        api_token = "test-token"
        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_cfo"
        ).mock(return_value=Response(200, json=SAMPLE_CFO_BUYS_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            cfo_buys = await client.insiders.get_cfo_buys()

            assert isinstance(cfo_buys, InsiderBuysResponse)
            assert cfo_buys.total == 250
            assert len(cfo_buys.data) == 2
            assert cfo_buys.data[0].position == "CFO"


class TestInsiderClusterBuyEndpoint:
    """Tests for insider cluster buy endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_cluster_buys(self, cache_dir: Path) -> None:
        """Test fetching cluster buys returns typed model."""
        api_token = "test-token"
        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_cluster_buy"
        ).mock(return_value=Response(200, json=SAMPLE_CLUSTER_BUY_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            cluster = await client.insiders.get_cluster_buys()

            assert isinstance(cluster, ClusterBuyResponse)
            assert cluster.total == 150
            assert len(cluster.data) == 3
            assert cluster.data[0].symbol == "FAKE1"
            assert cluster.data[0].insider_buy_count_unique == 8
            assert cluster.data[0].buy_total_shares == 125000


class TestInsiderDoubleBuyEndpoint:
    """Tests for insider double buy endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_double_buys(self, cache_dir: Path) -> None:
        """Test fetching double buys returns typed model."""
        api_token = "test-token"
        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_double"
        ).mock(return_value=Response(200, json=SAMPLE_DOUBLE_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            double = await client.insiders.get_double_buys()

            assert isinstance(double, DoubleBuyResponse)
            assert double.total == 100
            assert len(double.data) == 3
            assert double.data[0].symbol == "FAKE1"
            assert double.data[0].buy_add_count == 3
            assert double.data[0].insider_buy_shares == 125000


class TestInsiderTripleBuyEndpoint:
    """Tests for insider triple buy endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_triple_buys(self, cache_dir: Path) -> None:
        """Test fetching triple buys returns typed model."""
        api_token = "test-token"
        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_triple"
        ).mock(return_value=Response(200, json=SAMPLE_TRIPLE_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            triple = await client.insiders.get_triple_buys()

            assert isinstance(triple, TripleBuyResponse)
            assert triple.total == 75
            assert len(triple.data) == 3
            assert triple.data[0].symbol == "FAKE1"
            assert triple.data[0].buy_add_count == 5
            assert triple.data[0].total_buyback_1y == "2.50"


class TestInsiderListEndpoint:
    """Tests for insider list endpoint."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_list(self, cache_dir: Path) -> None:
        """Test fetching insider list returns typed model."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/insider_list").mock(
            return_value=Response(200, json=SAMPLE_LIST_RESPONSE)
        )

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            insiders = await client.insiders.get_list()

            assert isinstance(insiders, InsiderListResponse)
            assert insiders.current_page == 1
            assert insiders.last_page == 50
            assert len(insiders.data) == 4
            assert insiders.data[0].cik == "0001234567"
            assert insiders.data[0].name == "John Smith"
            assert "FAKE1" in insiders.data[0].companies

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_list_cached(self, cache_dir: Path) -> None:
        """Test that insider list is cached."""
        api_token = "test-token"
        route = respx.get(f"https://api.gurufocus.com/public/user/{api_token}/insider_list").mock(
            return_value=Response(200, json=SAMPLE_LIST_RESPONSE)
        )

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            await client.insiders.get_list()
            await client.insiders.get_list()
            assert route.call_count == 1


class TestInsiderIterators:
    """Tests for async iterator methods."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    @respx.mock
    async def test_iter_ceo_buys(self, cache_dir: Path) -> None:
        """Test iterating through CEO buys."""
        api_token = "test-token"

        # Page 1 response
        page1_response = {
            "total": 5,
            "per_page": 3,
            "current_page": 1,
            "last_page": 2,
            "from": 1,
            "to": 3,
            "data": SAMPLE_CEO_BUYS_RESPONSE["data"],
        }

        # Page 2 response (last page)
        page2_response = {
            "total": 5,
            "per_page": 3,
            "current_page": 2,
            "last_page": 2,
            "from": 4,
            "to": 5,
            "data": [SAMPLE_CEO_BUYS_RESPONSE["data"][0], SAMPLE_CEO_BUYS_RESPONSE["data"][1]],
        }

        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_ceo",
            params={"page": 1},
        ).mock(return_value=Response(200, json=page1_response))

        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_ceo",
            params={"page": 2},
        ).mock(return_value=Response(200, json=page2_response))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            items = []
            async for buy in client.insiders.iter_ceo_buys():
                items.append(buy)

            # Should have 3 from page 1 + 2 from page 2 = 5 items
            assert len(items) == 5
            assert items[0].symbol == "FAKE1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_iter_ceo_buys_max_pages(self, cache_dir: Path) -> None:
        """Test max_pages limit on iterator."""
        api_token = "test-token"

        page1_response = {
            "total": 100,
            "per_page": 3,
            "current_page": 1,
            "last_page": 34,
            "from": 1,
            "to": 3,
            "data": SAMPLE_CEO_BUYS_RESPONSE["data"],
        }

        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_buys/insider_ceo",
            params={"page": 1},
        ).mock(return_value=Response(200, json=page1_response))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            items = []
            async for buy in client.insiders.iter_ceo_buys(max_pages=1):
                items.append(buy)

            # Should only have items from first page (max_pages=1)
            assert len(items) == 3

    @pytest.mark.asyncio
    @respx.mock
    async def test_iter_list(self, cache_dir: Path) -> None:
        """Test iterating through insider list."""
        api_token = "test-token"

        # Single page response (last_page=1)
        single_page_response = {
            "data": SAMPLE_LIST_RESPONSE["data"],
            "currentPage": 1,
            "lastPage": 1,
        }

        respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/insider_list",
            params={"page": 1},
        ).mock(return_value=Response(200, json=single_page_response))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            items = []
            async for insider in client.insiders.iter_list():
                items.append(insider)

            assert len(items) == 4
            assert items[0].name == "John Smith"
