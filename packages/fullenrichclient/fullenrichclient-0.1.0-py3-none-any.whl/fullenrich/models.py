"""Data models for the FullEnrich library."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias


class EnrichmentStatus(str, Enum):
    """Status of an enrichment request."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class ReverseStatus(str, Enum):
    """Status of a reverse lookup request."""

    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELED = "CANCELED"
    CREDITS_INSUFFICIENT = "CREDITS_INSUFFICIENT"
    FINISHED = "FINISHED"
    RATE_LIMIT = "RATE_LIMIT"
    UNKNOWN = "UNKNOWN"


class EnrichField(str, Enum):
    """Available fields to enrich."""

    EMAILS = "contact.emails"
    PERSONAL_EMAILS = "contact.personal_emails"
    PHONES = "contact.phones"


LinkedInUrl: TypeAlias = str
EnrichFieldInput: TypeAlias = EnrichField | str


def normalize_enrich_fields(fields: list[EnrichFieldInput]) -> list[str]:
    """Convert enrich fields to string values."""
    result = []
    for f in fields:
        if isinstance(f, EnrichField):
            result.append(f.value)
        else:
            result.append(f)
    return result


@dataclass
class EnrichmentRequest:
    """A single enrichment request item.

    You can provide linkedin_url directly, or use firstname/lastname/domain/company_name
    to find the person.
    """

    linkedin_url: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    domain: str | None = None
    company_name: str | None = None
    enrich_fields: list[EnrichFieldInput] = field(
        default_factory=lambda: [EnrichField.EMAILS, EnrichField.PHONES]
    )
    custom: dict[str, str] | None = None

    def to_dict(self) -> dict:
        result: dict = {
            "enrich_fields": normalize_enrich_fields(self.enrich_fields),
        }

        if self.linkedin_url:
            result["linkedin_url"] = self.linkedin_url
        if self.firstname:
            result["firstname"] = self.firstname
        if self.lastname:
            result["lastname"] = self.lastname
        if self.domain:
            result["domain"] = self.domain
        if self.company_name:
            result["company_name"] = self.company_name
        if self.custom:
            result["custom"] = self.custom

        return result


@dataclass
class EnrichmentResponse:
    """Response from an enrichment request."""

    enrichment_id: str
    status: EnrichmentStatus | None = None
    results: list[dict] | None = None
    raw_response: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "EnrichmentResponse":
        status = None
        if "status" in data:
            try:
                status = EnrichmentStatus(data["status"])
            except ValueError:
                status = None

        return cls(
            enrichment_id=data.get("enrichment_id", ""),
            status=status,
            results=data.get("results"),
            raw_response=data,
        )


@dataclass
class ReverseLookupResponse:
    """Response from a reverse lookup request."""

    reverse_id: str
    status: ReverseStatus | None = None
    datas: list[dict] | None = None
    cost: dict | None = None
    raw_response: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ReverseLookupResponse":
        status = None
        if "status" in data:
            try:
                status = ReverseStatus(data["status"])
            except ValueError:
                status = None

        return cls(
            reverse_id=data.get("enrichment_id", data.get("id", "")),
            status=status,
            datas=data.get("datas"),
            cost=data.get("cost"),
            raw_response=data,
        )


@dataclass
class CreditsResponse:
    """Response from credits endpoint."""

    balance: int
    raw_response: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "CreditsResponse":
        return cls(
            balance=data.get("balance", 0),
            raw_response=data,
        )
