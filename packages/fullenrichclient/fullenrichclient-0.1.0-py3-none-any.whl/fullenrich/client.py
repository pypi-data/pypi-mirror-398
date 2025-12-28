"""FullEnrich API client."""

import logging
import os
import time
from typing import Sequence

from dotenv import load_dotenv
import httpx

from .exceptions import (
    AuthenticationError,
    EnrichmentFailedError,
    EnrichmentTimeoutError,
)
from .models import (
    CreditsResponse,
    EnrichField,
    EnrichFieldInput,
    EnrichmentRequest,
    EnrichmentResponse,
    EnrichmentStatus,
    ReverseLookupResponse,
    ReverseStatus,
)

load_dotenv()

logger = logging.getLogger(__name__)


class FullEnrich:
    """Client for interacting with the FullEnrich API."""

    DEFAULT_BASE_URL = "https://app.fullenrich.com/api/v1"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the FullEnrich client.

        Args:
            api_key: Your FullEnrich API key. If None, reads from FULLENRICH_API_KEY env var.
            base_url: Optional custom base URL for the API.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("FULLENRICH_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set via FULLENRICH_API_KEY environment variable"
            )
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            self._client.close()

    def __enter__(self) -> "FullEnrich":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # Account Methods
    # -------------------------------------------------------------------------

    def get_credits(self) -> CreditsResponse:
        """Get current credit balance.

        Returns:
            CreditsResponse with the balance.
        """
        response = self._get_client().get(
            f"{self.base_url}/account/credits",
            headers=self._headers,
        )
        data = self._handle_response(response)
        return CreditsResponse.from_dict(data)

    # -------------------------------------------------------------------------
    # Enrichment Methods
    # -------------------------------------------------------------------------

    def enrich(
        self,
        linkedin_urls: str | Sequence[str],
        enrich_fields: list[EnrichFieldInput] | None = None,
        name: str = "enrichment",
        webhook_url: str | None = None,
        custom: dict[str, str] | None = None,
    ) -> EnrichmentResponse:
        """Start a bulk enrichment request using LinkedIn URLs.

        Args:
            linkedin_urls: Single LinkedIn URL or list of URLs to enrich.
            enrich_fields: Fields to enrich. Can be EnrichField enum or strings
                like "contact.emails", "contact.phones", "contact.personal_emails".
                Defaults to emails and phones.
            name: Name for the enrichment request.
            webhook_url: Optional webhook URL to receive results.
            custom: Optional custom data dict (all values must be strings, max 20 entries).

        Returns:
            EnrichmentResponse with the enrichment_id.
        """
        if enrich_fields is None:
            enrich_fields = [EnrichField.EMAILS, EnrichField.PHONES]

        if isinstance(linkedin_urls, str):
            linkedin_urls = [linkedin_urls]

        requests = [
            EnrichmentRequest(
                linkedin_url=url, enrich_fields=enrich_fields, custom=custom
            )
            for url in linkedin_urls
        ]

        return self.enrich_batch(requests, name=name, webhook_url=webhook_url)

    def enrich_batch(
        self,
        requests: Sequence[EnrichmentRequest],
        name: str = "enrichment",
        webhook_url: str | None = None,
    ) -> EnrichmentResponse:
        """Start a bulk enrichment request with full control over each item.

        Use this method when you need to:
        - Enrich by name/domain instead of LinkedIn URL
        - Specify different enrich_fields per person
        - Include custom data per person

        Args:
            requests: List of EnrichmentRequest objects.
            name: Name for the enrichment request.
            webhook_url: Optional webhook URL to receive results.

        Returns:
            EnrichmentResponse with the enrichment_id.

        Example:
            requests = [
                EnrichmentRequest(linkedin_url="https://linkedin.com/in/user1"),
                EnrichmentRequest(
                    firstname="John",
                    lastname="Doe",
                    domain="example.com",
                    enrich_fields=[EnrichField.EMAILS],
                    custom={"crm_id": "123"}
                ),
            ]
            response = client.enrich_batch(requests)
        """
        payload: dict = {
            "name": name,
            "datas": [req.to_dict() for req in requests],
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url

        logger.info("Starting enrichment for %d request(s)", len(requests))

        response = self._get_client().post(
            f"{self.base_url}/contact/enrich/bulk",
            headers=self._headers,
            json=payload,
        )
        data = self._handle_response(response)
        logger.info("Enrichment started: %s", data.get("enrichment_id"))

        return EnrichmentResponse.from_dict(data)

    def get_enrichment(self, enrichment_id: str) -> EnrichmentResponse:
        """Get the status and results of an enrichment request.

        Args:
            enrichment_id: The ID of the enrichment request.

        Returns:
            EnrichmentResponse with status and results.
        """
        response = self._get_client().get(
            f"{self.base_url}/contact/enrich/bulk/{enrichment_id}",
            headers=self._headers,
        )
        data = self._handle_response(response)
        return EnrichmentResponse.from_dict(data)

    def wait_for_enrichment(
        self,
        enrichment_id: str,
        max_attempts: int = 30,
        poll_interval: int = 10,
    ) -> EnrichmentResponse:
        """Poll for enrichment results until complete.

        Args:
            enrichment_id: The ID of the enrichment request.
            max_attempts: Maximum number of polling attempts.
            poll_interval: Seconds between polling attempts.

        Returns:
            EnrichmentResponse with final results.

        Raises:
            EnrichmentFailedError: If the enrichment fails.
            EnrichmentTimeoutError: If max attempts exceeded.
        """
        for attempt in range(max_attempts):
            logger.info(
                "Polling attempt %d/%d for %s",
                attempt + 1,
                max_attempts,
                enrichment_id,
            )

            result = self.get_enrichment(enrichment_id)
            logger.info("Status: %s", result.status)

            if result.status == EnrichmentStatus.FINISHED:
                return result
            elif result.status == EnrichmentStatus.FAILED:
                raise EnrichmentFailedError(
                    f"Enrichment {enrichment_id} failed",
                    result=result.raw_response,
                )

            time.sleep(poll_interval)

        raise EnrichmentTimeoutError(enrichment_id, max_attempts)

    def enrich_and_wait(
        self,
        linkedin_urls: str | Sequence[str],
        enrich_fields: list[EnrichFieldInput] | None = None,
        name: str = "enrichment",
        webhook_url: str | None = None,
        max_attempts: int = 30,
        poll_interval: int = 10,
    ) -> EnrichmentResponse:
        """Start enrichment and wait for results.

        Convenience method that combines enrich() and wait_for_enrichment().

        Args:
            linkedin_urls: Single LinkedIn URL or list of URLs to enrich.
            enrich_fields: Fields to enrich. Defaults to emails and phones.
            name: Name for the enrichment request.
            webhook_url: Optional webhook URL to receive results.
            max_attempts: Maximum number of polling attempts.
            poll_interval: Seconds between polling attempts.

        Returns:
            EnrichmentResponse with final results.
        """
        response = self.enrich(
            linkedin_urls=linkedin_urls,
            enrich_fields=enrich_fields,
            name=name,
            webhook_url=webhook_url,
        )

        return self.wait_for_enrichment(
            enrichment_id=response.enrichment_id,
            max_attempts=max_attempts,
            poll_interval=poll_interval,
        )

    # -------------------------------------------------------------------------
    # Reverse Lookup Methods
    # -------------------------------------------------------------------------

    def reverse_lookup(
        self,
        emails: str | Sequence[str],
        name: str = "reverse-lookup",
        webhook_url: str | None = None,
    ) -> ReverseLookupResponse:
        """Start a reverse email lookup to find LinkedIn profiles.

        Args:
            emails: Single email or list of emails to lookup.
            name: Name for the lookup operation.
            webhook_url: Optional webhook URL to receive results.

        Returns:
            ReverseLookupResponse with the reverse_id.
        """
        if isinstance(emails, str):
            emails = [emails]

        payload: dict = {
            "name": name,
            "data": [{"email": email} for email in emails],
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url

        logger.info("Starting reverse lookup for %d email(s)", len(emails))

        response = self._get_client().post(
            f"{self.base_url}/contact/reverse/email/bulk",
            headers=self._headers,
            json=payload,
        )
        data = self._handle_response(response)
        logger.info("Reverse lookup started: %s", data.get("enrichment_id"))

        return ReverseLookupResponse.from_dict(data)

    def get_reverse_lookup(self, reverse_id: str) -> ReverseLookupResponse:
        """Get the status and results of a reverse lookup.

        Args:
            reverse_id: The ID of the reverse lookup request.

        Returns:
            ReverseLookupResponse with status and results.
        """
        response = self._get_client().get(
            f"{self.base_url}/contact/reverse/email/bulk/{reverse_id}",
            headers=self._headers,
        )
        data = self._handle_response(response)
        return ReverseLookupResponse.from_dict(data)

    def wait_for_reverse_lookup(
        self,
        reverse_id: str,
        max_attempts: int = 30,
        poll_interval: int = 10,
    ) -> ReverseLookupResponse:
        """Poll for reverse lookup results until complete.

        Args:
            reverse_id: The ID of the reverse lookup request.
            max_attempts: Maximum number of polling attempts.
            poll_interval: Seconds between polling attempts.

        Returns:
            ReverseLookupResponse with final results.

        Raises:
            EnrichmentFailedError: If the lookup fails.
            EnrichmentTimeoutError: If max attempts exceeded.
        """
        for attempt in range(max_attempts):
            logger.info(
                "Polling attempt %d/%d for reverse lookup %s",
                attempt + 1,
                max_attempts,
                reverse_id,
            )

            result = self.get_reverse_lookup(reverse_id)
            logger.info("Status: %s", result.status)

            if result.status == ReverseStatus.FINISHED:
                return result
            elif result.status in (
                ReverseStatus.CANCELED,
                ReverseStatus.CREDITS_INSUFFICIENT,
            ):
                raise EnrichmentFailedError(
                    f"Reverse lookup {reverse_id} failed with status {result.status}",
                    result=result.raw_response,
                )

            time.sleep(poll_interval)

        raise EnrichmentTimeoutError(reverse_id, max_attempts)

    def reverse_lookup_and_wait(
        self,
        emails: str | Sequence[str],
        name: str = "reverse-lookup",
        webhook_url: str | None = None,
        max_attempts: int = 30,
        poll_interval: int = 10,
    ) -> ReverseLookupResponse:
        """Start reverse lookup and wait for results.

        Convenience method that combines reverse_lookup() and wait_for_reverse_lookup().

        Args:
            emails: Single email or list of emails to lookup.
            name: Name for the lookup operation.
            webhook_url: Optional webhook URL to receive results.
            max_attempts: Maximum number of polling attempts.
            poll_interval: Seconds between polling attempts.

        Returns:
            ReverseLookupResponse with final results.
        """
        response = self.reverse_lookup(
            emails=emails,
            name=name,
            webhook_url=webhook_url,
        )

        return self.wait_for_reverse_lookup(
            reverse_id=response.reverse_id,
            max_attempts=max_attempts,
            poll_interval=poll_interval,
        )
