import httpx
import logging
from typing import Optional, Dict, Any, List
from .models import OffersResponse


class KaspiClient:
    BASE_URL = "https://kaspi.kz"

    def __init__(
        self,
        timeout: int = 30,
        proxy: Optional[str] = None,
        verbose: bool = False,
        max_retries: Optional[int] = 3,
        retry_status_codes: Optional[List[int]] = None,
        backoff_factor: float = 0.5,
        max_backoff_wait: float = 60.0,
    ):
        self.timeout = timeout
        self.proxy = proxy
        self.verbose = verbose
        self.headers = {
            "Content-Type": "application/json",
            "Referer": "https://kaspi.kz/shop/search/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        # Set up logging first (needed for retry configuration warnings)
        self.logger = logging.getLogger(__name__)

        # Configure retry behavior
        self.max_retries = max_retries
        self.retry_status_codes = retry_status_codes or [429, 500, 502, 503, 504]
        self.backoff_factor = backoff_factor
        self.max_backoff_wait = max_backoff_wait

        # Initialize retry transport if retries are enabled
        if max_retries is not None and max_retries > 0:
            try:
                from httpx_retries import Retry, RetryTransport
                retry = Retry(
                    total=max_retries,
                    status_forcelist=self.retry_status_codes,
                    backoff_factor=backoff_factor,
                    max_backoff_wait=max_backoff_wait,
                    backoff_jitter=1.0,
                    respect_retry_after_header=True,
                    allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
                )
                self._retry_transport = RetryTransport(retry=retry)
            except ImportError:
                self.logger.warning(
                    "httpx-retries not installed. Retry functionality disabled. "
                    "Install with: pip install httpx-retries"
                )
                self._retry_transport = None
        else:
            self._retry_transport = None

        # Configure verbose logging mode
        if self.verbose:
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug(f"KaspiClient initialized with timeout={timeout}, proxy={proxy}")
            if self._retry_transport:
                self.logger.debug(
                    f"Retry enabled: max_retries={max_retries}, "
                    f"backoff_factor={backoff_factor}, "
                    f"retry_status_codes={self.retry_status_codes}"
                )
            else:
                self.logger.debug("Retry disabled")
        else:
            self.logger.setLevel(logging.WARNING)

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection and proxy configuration.

        Returns:
            Dict containing connection test results including:
            - success: bool
            - proxy: str or None
            - status_code: int
            - error: str (if failed)

        Raises:
            httpx.HTTPError: If the test request fails
        """
        test_url = "https://httpbin.org/get"
        self.logger.debug(f"Testing connection to {test_url}")
        self.logger.debug(f"Using proxy: {self.proxy if self.proxy else 'None (direct connection)'}")

        try:
            client_kwargs = {
                "timeout": self.timeout,
                "proxy": self.proxy,
            }
            if self._retry_transport:
                client_kwargs["transport"] = self._retry_transport

            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(test_url)
                response.raise_for_status()
                data = response.json()

                result = {
                    "success": True,
                    "proxy": self.proxy,
                    "status_code": response.status_code,
                    "origin_ip": data.get("origin"),
                    "url_accessed": test_url
                }

                self.logger.debug(f"Connection test successful: {result}")
                return result

        except Exception as e:
            result = {
                "success": False,
                "proxy": self.proxy,
                "error": str(e)
            }
            self.logger.error(f"Connection test failed: {result}")
            raise

    async def get_offers(
            self,
            product_id: str,
            city_id: str = "750000000",
            limit: int = 64,
            page: int = 0
    ) -> OffersResponse:
        url = f"{self.BASE_URL}/yml/offer-view/offers/{product_id}"

        payload = {
            "cityId": city_id,
            "id": product_id,
            "limit": limit,
            "page": page,
            "sortOption": "PRICE"
        }

        self.logger.debug(f"Requesting offers for product_id={product_id}")
        self.logger.debug(f"URL: {url}")
        self.logger.debug(f"Payload: {payload}")
        self.logger.debug(f"Using proxy: {self.proxy if self.proxy else 'None (direct connection)'}")

        client_kwargs = {
            "timeout": self.timeout,
            "proxy": self.proxy,
        }
        if self._retry_transport:
            client_kwargs["transport"] = self._retry_transport

        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            self.logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            result = OffersResponse.from_dict(response.json())
            self.logger.debug(f"Successfully retrieved {len(result.offers)} offers")
            return result
