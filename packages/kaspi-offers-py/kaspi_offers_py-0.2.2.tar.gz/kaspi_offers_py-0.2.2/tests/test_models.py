"""Tests for data models."""

import pytest
from kaspi_offers_py import Offer, OffersResponse


class TestOffer:
    """Tests for Offer dataclass."""

    def test_from_dict_with_all_fields(self, sample_offer_dict):
        """Test Offer deserialization with all fields populated."""
        offer = Offer.from_dict(sample_offer_dict)

        assert offer.masterSku == "123456789"
        assert offer.merchantId == "987654321"
        assert offer.merchantName == "Test Electronics Store"
        assert offer.merchantSku == "SKU-TEST-001"
        assert offer.title == "iPhone 15 Pro Max 256GB"
        assert offer.price == 599990.0
        assert offer.merchantRating == 4.8
        assert offer.merchantReviewsQuantity == 1523
        assert offer.deliveryType == "EXPRESS"
        assert offer.deliveryDuration == "1-2 дня"
        assert offer.kaspiDelivery is True
        assert offer.preorder == 0
        assert offer.delivery == "Бесплатно"
        assert offer.pickup == "Доступен самовывоз"

    def test_from_dict_with_optional_fields_missing(self, sample_offer_minimal_dict):
        """Test Offer deserialization with optional fields missing."""
        offer = Offer.from_dict(sample_offer_minimal_dict)

        assert offer.masterSku == "111222333"
        assert offer.merchantId == "555666777"
        assert offer.deliveryDuration is None
        assert offer.delivery is None
        assert offer.pickup is None

    def test_from_dict_with_edge_cases(self, sample_offer_edge_case_dict):
        """Test Offer deserialization with edge cases."""
        offer = Offer.from_dict(sample_offer_edge_case_dict)

        # Special characters in merchant name
        assert offer.merchantName == 'Магазин "Электроника" & Co.'
        # Special characters in title
        assert offer.title == "Товар с спец. символами! @#$%"
        # Zero price
        assert offer.price == 0.0
        # Perfect rating
        assert offer.merchantRating == 5.0
        # No reviews
        assert offer.merchantReviewsQuantity == 0
        # Preorder item
        assert offer.preorder == 1

    def test_from_dict_missing_required_field(self, sample_offer_dict):
        """Test Offer deserialization raises error when required field is missing."""
        del sample_offer_dict["masterSku"]

        with pytest.raises(KeyError):
            Offer.from_dict(sample_offer_dict)

    def test_from_dict_with_various_prices(self):
        """Test Offer handles various price values."""
        offer_data = {
            "masterSku": "123",
            "merchantId": "456",
            "merchantName": "Store",
            "merchantSku": "789",
            "title": "Product",
            "price": 1234567.89,  # Large price with decimals
            "merchantRating": 4.5,
            "merchantReviewsQuantity": 100,
            "deliveryType": "EXPRESS",
            "deliveryDuration": "1 day",
            "kaspiDelivery": True,
            "preorder": 0,
        }

        offer = Offer.from_dict(offer_data)
        assert offer.price == 1234567.89

    def test_from_dict_with_various_ratings(self):
        """Test Offer handles various rating values."""
        test_cases = [0.0, 2.5, 4.7, 5.0]

        for rating in test_cases:
            offer_data = {
                "masterSku": "123",
                "merchantId": "456",
                "merchantName": "Store",
                "merchantSku": "789",
                "title": "Product",
                "price": 1000.0,
                "merchantRating": rating,
                "merchantReviewsQuantity": 100,
                "deliveryType": "EXPRESS",
                "deliveryDuration": "1 day",
                "kaspiDelivery": True,
                "preorder": 0,
            }

            offer = Offer.from_dict(offer_data)
            assert offer.merchantRating == rating


class TestOffersResponse:
    """Tests for OffersResponse dataclass."""

    def test_from_dict_with_multiple_offers(self, sample_response_dict):
        """Test OffersResponse deserialization with multiple offers."""
        response = OffersResponse.from_dict(sample_response_dict)

        assert len(response.offers) == 3
        assert response.total == 150
        assert response.offersCount == 3

        # Verify first offer is properly deserialized
        first_offer = response.offers[0]
        assert isinstance(first_offer, Offer)
        assert first_offer.masterSku == "123456789"

    def test_from_dict_with_empty_offers(self, sample_response_empty_dict):
        """Test OffersResponse deserialization with empty offers list."""
        response = OffersResponse.from_dict(sample_response_empty_dict)

        assert response.offers == []
        assert response.total == 0
        assert response.offersCount == 0

    def test_from_dict_with_single_offer(self, sample_response_single_dict):
        """Test OffersResponse deserialization with single offer."""
        response = OffersResponse.from_dict(sample_response_single_dict)

        assert len(response.offers) == 1
        assert response.total == 1
        assert response.offersCount == 1
        assert isinstance(response.offers[0], Offer)

    def test_from_dict_with_pagination(self, sample_response_paginated_dict):
        """Test OffersResponse with pagination (more total than current offers)."""
        response = OffersResponse.from_dict(sample_response_paginated_dict)

        assert len(response.offers) == 2
        assert response.total == 250
        assert response.offersCount == 2
        # Total is greater than current offers count (pagination)
        assert response.total > len(response.offers)

    def test_from_dict_missing_required_field(self, sample_response_dict):
        """Test OffersResponse raises error when required field is missing."""
        del sample_response_dict["offers"]

        with pytest.raises(KeyError):
            OffersResponse.from_dict(sample_response_dict)

    def test_from_dict_all_offers_properly_instantiated(self, sample_response_dict):
        """Test all offers in response are properly instantiated as Offer objects."""
        response = OffersResponse.from_dict(sample_response_dict)

        for offer in response.offers:
            assert isinstance(offer, Offer)
            assert hasattr(offer, "masterSku")
            assert hasattr(offer, "merchantId")
            assert hasattr(offer, "price")

    def test_from_dict_with_invalid_offer_in_list(self):
        """Test OffersResponse raises error when an offer is malformed."""
        invalid_response = {
            "offers": [
                {
                    "masterSku": "123",
                    # Missing required fields
                }
            ],
            "total": 1,
            "offersCount": 1,
        }

        with pytest.raises(KeyError):
            OffersResponse.from_dict(invalid_response)
