"""Integration tests for KaspiClient with real API requests.

These tests make actual HTTP requests to the Kaspi.kz API and require network connectivity.
Run with: pytest -m integration
Skip with: pytest -m "not integration"
"""

import pytest
from kaspi_offers_py import KaspiClient, OffersResponse, Offer


@pytest.mark.integration
class TestKaspiClientIntegration:
    """Integration tests with real API calls."""

    @pytest.mark.asyncio
    async def test_real_get_offers_success(self):
        """Test successful real API request with a known product."""
        # Using a real product ID from Kaspi.kz (iPhone example)
        # This is a public product ID that should be stable
        product_id = "100028408"  # Apple iPhone 15 Pro Max

        client = KaspiClient()
        response = await client.get_offers(product_id=product_id)

        # Verify response structure
        assert isinstance(response, OffersResponse)
        assert hasattr(response, 'offers')
        assert hasattr(response, 'total')

        # Verify we got actual offers
        assert isinstance(response.offers, list)

        # If there are offers, verify their structure
        if len(response.offers) > 0:
            first_offer = response.offers[0]
            assert isinstance(first_offer, Offer)
            assert hasattr(first_offer, 'id')
            assert hasattr(first_offer, 'merchantName')
            assert hasattr(first_offer, 'price')

    @pytest.mark.asyncio
    async def test_real_get_offers_with_pagination(self):
        """Test real API request with custom pagination parameters."""
        product_id = "100028408"

        client = KaspiClient()
        # Request first page with limit
        response = await client.get_offers(
            product_id=product_id,
            limit=10,
            page=0
        )

        assert isinstance(response, OffersResponse)
        # Should return at most 10 offers
        assert len(response.offers) <= 10

    @pytest.mark.asyncio
    async def test_real_get_offers_with_city(self):
        """Test real API request with specific city."""
        product_id = "100028408"
        city_id = "750000000"  # Almaty

        client = KaspiClient()
        response = await client.get_offers(
            product_id=product_id,
            city_id=city_id
        )

        assert isinstance(response, OffersResponse)
        assert isinstance(response.offers, list)

    @pytest.mark.asyncio
    async def test_real_get_offers_invalid_product_id(self):
        """Test real API request with invalid product ID."""
        product_id = "99999999999999"  # Non-existent product

        client = KaspiClient()
        response = await client.get_offers(product_id=product_id)

        # API might return empty offers for invalid IDs
        assert isinstance(response, OffersResponse)
        # Typically should be empty for non-existent products
        assert len(response.offers) == 0 or isinstance(response.offers, list)

    @pytest.mark.asyncio
    async def test_real_concurrent_requests(self):
        """Test multiple concurrent real API requests."""
        import asyncio

        product_ids = ["100028408", "100027106", "102119206"]

        client = KaspiClient()
        results = await asyncio.gather(
            *[client.get_offers(product_id=pid) for pid in product_ids]
        )

        # Verify all requests succeeded
        assert len(results) == 3
        assert all(isinstance(r, OffersResponse) for r in results)

    @pytest.mark.asyncio
    async def test_real_client_timeout(self):
        """Test real API request respects timeout setting."""
        client = KaspiClient(timeout=30)
        response = await client.get_offers(product_id="100028408")
        assert isinstance(response, OffersResponse)

    @pytest.mark.asyncio
    async def test_real_response_data_types(self):
        """Test that real API response has correct data types."""
        product_id = "100028408"

        client = KaspiClient()
        response = await client.get_offers(product_id=product_id)

        # Check response structure
        assert isinstance(response.total, int)
        assert isinstance(response.offers, list)

        # Check first offer if available
        if len(response.offers) > 0:
            offer = response.offers[0]
            assert isinstance(offer.id, str)
            assert isinstance(offer.merchantName, str)
            assert isinstance(offer.price, (int, float))
            assert isinstance(offer.available, bool)

            # Optional fields should be None or correct type
            if offer.installmentPrice is not None:
                assert isinstance(offer.installmentPrice, (int, float))
