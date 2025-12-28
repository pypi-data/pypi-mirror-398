"""Custom exceptions for the FullEnrich library."""


class FullEnrichError(Exception):
    """Base exception for FullEnrich errors."""

    pass


class EnrichmentFailedError(FullEnrichError):
    """Raised when an enrichment request fails."""

    def __init__(self, message: str, result: dict | None = None):
        super().__init__(message)
        self.result = result


class EnrichmentTimeoutError(FullEnrichError):
    """Raised when polling for enrichment results times out."""

    def __init__(self, enrichment_id: str, attempts: int):
        super().__init__(
            f"Enrichment {enrichment_id} did not complete after {attempts} attempts"
        )
        self.enrichment_id = enrichment_id
        self.attempts = attempts


class AuthenticationError(FullEnrichError):
    """Raised when API authentication fails."""

    pass
