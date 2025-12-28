"""Tests for KaspiClient."""

import pytest
import httpx
from kaspi_offers_py import KaspiClient, OffersResponse, Offer


class TestKaspiClientInitialization:
    """Tests for KaspiClient initialization."""

    def test_default_timeout(self, kaspi_client):
        """Test client is initialized with default timeout."""
        assert kaspi_client.timeout == 30

    def test_custom_timeout(self, kaspi_client_custom_timeout):
        """Test client is initialized with custom timeout."""
        assert kaspi_client_custom_timeout.timeout == 10

    def test_base_url(self, kaspi_client):
        """Test client has correct base URL."""
        assert kaspi_client.BASE_URL == "https://kaspi.kz"

    def test_headers(self, kaspi_client):
        """Test client has correct headers."""
        assert kaspi_client.headers["Content-Type"] == "application/json"
        assert kaspi_client.headers["Referer"] == "https://kaspi.kz/shop/search/"

    def test_default_proxy(self, kaspi_client):
        """Test client is initialized with no proxy by default."""
        assert kaspi_client.proxy is None

    def test_custom_proxy(self, kaspi_client_with_proxy):
        """Test client is initialized with custom proxy."""
        assert kaspi_client_with_proxy.proxy == "http://proxy.example.com:8080"

    def test_default_verbose(self, kaspi_client):
        """Test client is initialized with verbose mode off by default."""
        assert kaspi_client.verbose is False

    def test_verbose_mode(self, kaspi_client_verbose):
        """Test client is initialized with verbose mode enabled."""
        assert kaspi_client_verbose.verbose is True
        assert kaspi_client_verbose.logger is not None


class TestKaspiClientGetOffers:
    """Tests for KaspiClient.get_offers() method."""

    @pytest.mark.asyncio
    async def test_get_offers_success(
        self, kaspi_client, sample_response_dict, httpx_mock
    ):
        """Test successful get_offers request."""
        product_id = "123456789"
        expected_url = f"{kaspi_client.BASE_URL}/yml/offer-view/offers/{product_id}"

        # Mock the POST request
        httpx_mock.add_response(
            method="POST",
            url=expected_url,
            json=sample_response_dict,
            status_code=200,
        )

        # Make the request
        response = await kaspi_client.get_offers(product_id=product_id)

        # Verify response type and content
        assert isinstance(response, OffersResponse)
        assert len(response.offers) == 3
        assert response.total == 150

    @pytest.mark.asyncio
    async def test_get_offers_url_construction(
        self, kaspi_client, sample_response_single_dict, httpx_mock
    ):
        """Test get_offers constructs correct URL."""
        product_id = "999888777"
        expected_url = f"https://kaspi.kz/yml/offer-view/offers/{product_id}"

        httpx_mock.add_response(
            method="POST", url=expected_url, json=sample_response_single_dict
        )

        await kaspi_client.get_offers(product_id=product_id)

        # Verify the request was made to the correct URL
        request = httpx_mock.get_request()
        assert str(request.url) == expected_url

    @pytest.mark.asyncio
    async def test_get_offers_default_parameters(
        self, kaspi_client, sample_response_single_dict, httpx_mock
    ):
        """Test get_offers uses default parameters."""
        product_id = "123"
        httpx_mock.add_response(json=sample_response_single_dict)

        await kaspi_client.get_offers(product_id=product_id)

        # Verify request payload contains default parameters
        request = httpx_mock.get_request()
        assert request.method == "POST"

        # Parse the JSON payload
        import json

        payload = json.loads(request.content)
        assert payload["cityId"] == "750000000"
        assert payload["id"] == product_id
        assert payload["limit"] == 64
        assert payload["page"] == 0

    @pytest.mark.asyncio
    async def test_get_offers_custom_parameters(
        self, kaspi_client, sample_response_single_dict, httpx_mock
    ):
        """Test get_offers accepts custom parameters."""
        product_id = "123"
        custom_city_id = "111222333"
        custom_limit = 10
        custom_page = 2

        httpx_mock.add_response(json=sample_response_single_dict)

        await kaspi_client.get_offers(
            product_id=product_id,
            city_id=custom_city_id,
            limit=custom_limit,
            page=custom_page,
        )

        # Verify request payload contains custom parameters
        request = httpx_mock.get_request()
        import json

        payload = json.loads(request.content)
        assert payload["cityId"] == custom_city_id
        assert payload["id"] == product_id
        assert payload["limit"] == custom_limit
        assert payload["page"] == custom_page

    @pytest.mark.asyncio
    async def test_get_offers_with_headers(
        self, kaspi_client, sample_response_single_dict, httpx_mock
    ):
        """Test get_offers sends correct headers."""
        httpx_mock.add_response(json=sample_response_single_dict)

        await kaspi_client.get_offers(product_id="123")

        # Verify headers
        request = httpx_mock.get_request()
        assert request.headers["content-type"] == "application/json"
        assert request.headers["referer"] == "https://kaspi.kz/shop/search/"

    @pytest.mark.asyncio
    async def test_get_offers_empty_response(
        self, kaspi_client, sample_response_empty_dict, httpx_mock
    ):
        """Test get_offers handles empty offers response."""
        httpx_mock.add_response(json=sample_response_empty_dict)

        response = await kaspi_client.get_offers(product_id="123")

        assert isinstance(response, OffersResponse)
        assert len(response.offers) == 0
        assert response.total == 0

    @pytest.mark.asyncio
    async def test_get_offers_response_parsing(
        self, kaspi_client, sample_response_dict, httpx_mock
    ):
        """Test get_offers properly parses response into OffersResponse."""
        httpx_mock.add_response(json=sample_response_dict)

        response = await kaspi_client.get_offers(product_id="123")

        # Verify response is properly parsed
        assert isinstance(response, OffersResponse)
        assert all(isinstance(offer, Offer) for offer in response.offers)
        assert response.offers[0].masterSku == "123456789"


class TestKaspiClientErrorHandling:
    """Tests for KaspiClient error handling."""

    @pytest.mark.asyncio
    async def test_get_offers_http_404_error(self, kaspi_client, httpx_mock):
        """Test get_offers raises error on 404 response."""
        httpx_mock.add_response(status_code=404)

        with pytest.raises(httpx.HTTPStatusError):
            await kaspi_client.get_offers(product_id="123")

    @pytest.mark.asyncio
    async def test_get_offers_http_500_error(self, kaspi_client, httpx_mock):
        """Test get_offers raises error on 500 response after retries."""
        # Add 500 response 4 times: 1 initial + 3 retries
        for _ in range(4):
            httpx_mock.add_response(status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await kaspi_client.get_offers(product_id="123")

    @pytest.mark.asyncio
    async def test_get_offers_http_400_error(self, kaspi_client, httpx_mock):
        """Test get_offers raises error on 400 bad request."""
        httpx_mock.add_response(status_code=400)

        with pytest.raises(httpx.HTTPStatusError):
            await kaspi_client.get_offers(product_id="123")

    @pytest.mark.asyncio
    async def test_get_offers_timeout(self, kaspi_client_custom_timeout, httpx_mock):
        """Test get_offers handles timeout after retries."""
        # Add exception 4 times: 1 initial + 3 retries
        for _ in range(4):
            httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        with pytest.raises(httpx.TimeoutException):
            await kaspi_client_custom_timeout.get_offers(product_id="123")

    @pytest.mark.asyncio
    async def test_get_offers_connection_error(self, kaspi_client, httpx_mock):
        """Test get_offers handles connection errors after retries."""
        # Add exception 4 times: 1 initial + 3 retries
        for _ in range(4):
            httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        with pytest.raises(httpx.ConnectError):
            await kaspi_client.get_offers(product_id="123")

    @pytest.mark.asyncio
    async def test_get_offers_invalid_json(self, kaspi_client, httpx_mock):
        """Test get_offers handles invalid JSON response."""
        httpx_mock.add_response(content=b"Not JSON", status_code=200)

        with pytest.raises(Exception):  # JSONDecodeError or similar
            await kaspi_client.get_offers(product_id="123")

    @pytest.mark.asyncio
    async def test_get_offers_malformed_response(self, kaspi_client, httpx_mock):
        """Test get_offers handles malformed response structure."""
        # Missing required fields
        httpx_mock.add_response(json={"invalid": "response"}, status_code=200)

        with pytest.raises(KeyError):
            await kaspi_client.get_offers(product_id="123")


class TestKaspiClientAsync:
    """Tests for async functionality."""

    @pytest.mark.asyncio
    async def test_get_offers_is_coroutine(self, kaspi_client):
        """Test get_offers returns a coroutine."""
        import inspect

        result = kaspi_client.get_offers(product_id="123")
        assert inspect.iscoroutine(result)
        # Close the coroutine to avoid warning
        result.close()

    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self, kaspi_client, sample_response_single_dict, httpx_mock
    ):
        """Test multiple concurrent get_offers calls."""
        import asyncio

        # Mock multiple responses
        for _ in range(3):
            httpx_mock.add_response(json=sample_response_single_dict)

        # Make concurrent requests
        results = await asyncio.gather(
            kaspi_client.get_offers(product_id="1"),
            kaspi_client.get_offers(product_id="2"),
            kaspi_client.get_offers(product_id="3"),
        )

        # Verify all requests succeeded
        assert len(results) == 3
        assert all(isinstance(r, OffersResponse) for r in results)

    @pytest.mark.asyncio
    async def test_get_offers_with_proxy(
        self, kaspi_client_with_proxy, sample_response_single_dict, httpx_mock
    ):
        """Test get_offers works with proxy configuration."""
        httpx_mock.add_response(json=sample_response_single_dict)

        response = await kaspi_client_with_proxy.get_offers(product_id="123")

        # Verify the request succeeded
        assert isinstance(response, OffersResponse)
        assert kaspi_client_with_proxy.proxy == "http://proxy.example.com:8080"


class TestKaspiClientConnectionTest:
    """Tests for KaspiClient.test_connection() method."""

    @pytest.mark.asyncio
    async def test_connection_success(self, kaspi_client, httpx_mock):
        """Test test_connection returns success with valid connection."""
        httpbin_response = {
            "args": {},
            "headers": {},
            "origin": "123.456.789.0",
            "url": "https://httpbin.org/get"
        }

        httpx_mock.add_response(
            url="https://httpbin.org/get",
            json=httpbin_response,
            status_code=200
        )

        result = await kaspi_client.test_connection()

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["origin_ip"] == "123.456.789.0"
        assert result["proxy"] is None
        assert result["url_accessed"] == "https://httpbin.org/get"

    @pytest.mark.asyncio
    async def test_connection_with_proxy(self, kaspi_client_with_proxy, httpx_mock):
        """Test test_connection works with proxy configuration."""
        httpbin_response = {
            "args": {},
            "headers": {},
            "origin": "111.222.333.444",
            "url": "https://httpbin.org/get"
        }

        httpx_mock.add_response(
            url="https://httpbin.org/get",
            json=httpbin_response,
            status_code=200
        )

        result = await kaspi_client_with_proxy.test_connection()

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["origin_ip"] == "111.222.333.444"
        assert result["proxy"] == "http://proxy.example.com:8080"

    @pytest.mark.asyncio
    async def test_connection_failure(self, kaspi_client, httpx_mock):
        """Test test_connection raises exception on connection failure after retries."""
        # Add exception 4 times: 1 initial + 3 retries (max_retries=3 means 3 retries after initial)
        for _ in range(4):
            httpx_mock.add_exception(
                httpx.ConnectError("Connection failed"),
                url="https://httpbin.org/get"
            )

        with pytest.raises(httpx.ConnectError):
            await kaspi_client.test_connection()

    @pytest.mark.asyncio
    async def test_connection_timeout(self, kaspi_client_custom_timeout, httpx_mock):
        """Test test_connection raises exception on timeout after retries."""
        # Add exception 4 times: 1 initial + 3 retries (max_retries=3 means 3 retries after initial)
        for _ in range(4):
            httpx_mock.add_exception(
                httpx.TimeoutException("Request timed out"),
                url="https://httpbin.org/get"
            )

        with pytest.raises(httpx.TimeoutException):
            await kaspi_client_custom_timeout.test_connection()


class TestKaspiClientVerboseMode:
    """Tests for KaspiClient verbose logging."""

    @pytest.mark.asyncio
    async def test_get_offers_verbose_logging(
        self, kaspi_client_verbose, sample_response_single_dict, httpx_mock, caplog
    ):
        """Test that verbose mode logs debug information."""
        import logging

        httpx_mock.add_response(json=sample_response_single_dict)

        with caplog.at_level(logging.DEBUG):
            await kaspi_client_verbose.get_offers(product_id="123")

        # Verify debug logs were created
        assert any("Requesting offers for product_id=123" in record.message
                   for record in caplog.records)
        assert any("Successfully retrieved" in record.message
                   for record in caplog.records)
