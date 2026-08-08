"""
DocIntel AI — Extraction Schemas.

Full Pydantic models for structured extraction of insurance product documents.
Matches PRD Section 15.
"""

from datetime import date
from decimal import Decimal
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

from app.schemas.query import Citation

T = TypeVar("T")

class FieldWithCitation(BaseModel, Generic[T]):
    """A field value with citation, confidence, and reasoning."""
    value: Optional[T] = None
    citation: Optional[Citation] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: Optional[str] = None  # if value is None, why?

# Sub-models
class Signatory(BaseModel):
    """Signatory of a document."""
    name: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None

class SignatoryWithCitation(BaseModel):
    """Signatory with citations per field."""
    name: FieldWithCitation[str]
    title: FieldWithCitation[str]
    organization: FieldWithCitation[str]

class BenefitItem(BaseModel):
    """A single benefit item in the benefit matrix."""
    benefit_number: int
    benefit_name: Optional[str] = None
    coverage_area: Optional[str] = None  # ASEAN+, APAC, Worldwide, etc.
    plan_tier: Optional[str] = None  # Platinum, Gold, Basic
    limit_amount: Optional[float] = None  # None if "Tidak Tersedia"
    limit_currency: Optional[str] = None  # IDR, USD
    limit_unit: Optional[str] = None  # per_person, per_family, per_incident, etc.
    conditions: Optional[str] = None  # e.g. "Tidak Tersedia", "Sesuai tagihan"

class BenefitItemWithCitation(BaseModel):
    """Benefit item with citations per field."""
    benefit_number: int
    benefit_name: FieldWithCitation[str]
    coverage_area: FieldWithCitation[str]
    plan_tier: FieldWithCitation[str]
    limit_amount: FieldWithCitation[Optional[float]]
    limit_currency: FieldWithCitation[str]
    limit_unit: FieldWithCitation[str]
    conditions: FieldWithCitation[Optional[str]]

class PremiumRow(BaseModel):
    """A single premium row in the premium matrix."""
    coverage_area: Optional[str] = None
    plan_tier: Optional[str] = None
    insured_type: Optional[str] = None  # Individual, Dual, Family
    duration_range: Optional[str] = None  # "1-3 hari", "Tahunan", etc.
    base_premium_idr: Optional[float] = None
    age_range: Optional[str] = None  # "0-69 tahun"

class PremiumRowWithCitation(BaseModel):
    """Premium row with citations per field."""
    coverage_area: FieldWithCitation[str]
    plan_tier: FieldWithCitation[str]
    insured_type: FieldWithCitation[str]
    duration_range: FieldWithCitation[str]
    base_premium_idr: FieldWithCitation[float]
    age_range: FieldWithCitation[str]

class AddOnBenefit(BaseModel):
    """Add-on benefit item."""
    add_on_name: Optional[str] = None
    coverage_area: Optional[str] = None
    plan_tier: Optional[str] = None
    limit_amount: Optional[float] = None
    additional_premium_idr: Optional[float] = None

class AddOnBenefitWithCitation(BaseModel):
    """Add-on benefit with citations."""
    add_on_name: FieldWithCitation[str]
    coverage_area: FieldWithCitation[str]
    plan_tier: FieldWithCitation[str]
    limit_amount: FieldWithCitation[Optional[float]]
    additional_premium_idr: FieldWithCitation[Optional[float]]

class SpecialCondition(BaseModel):
    """Special condition (e.g. age loading)."""
    condition_name: Optional[str] = None  # e.g. "Age 70-75 Loading"
    condition_type: Optional[str] = None
    parameters: Optional[dict] = None  # e.g. {"age_min": 70, "loading_percent": 35}

class SpecialConditionWithCitation(BaseModel):
    """Special condition with citations."""
    condition_name: FieldWithCitation[str]
    condition_type: FieldWithCitation[str]
    parameters: FieldWithCitation[dict]

# Main Extraction Schema
class InsuranceProductExtraction(BaseModel):
    """
    Full extraction schema for insurance product documents.
    Matches PRD Section 15.
    """
    # Identity
    product_name: FieldWithCitation[str]
    product_name_english: FieldWithCitation[Optional[str]]
    insurer: FieldWithCitation[str]
    insured_target: FieldWithCitation[str]  # e.g. "Nasabah PT Bank X"

    # Coverage
    coverage_areas: FieldWithCitation[list[str]]
    insured_types: FieldWithCitation[list[str]]  # Individual, Dual, Family
    coverage_period_short_trip_max_days: FieldWithCitation[int]  # e.g. 183
    coverage_period_annual_max_days_per_trip: FieldWithCitation[int]  # e.g. 90

    # Age
    max_age_adult: FieldWithCitation[int]  # e.g. 75
    max_age_child: FieldWithCitation[int]  # e.g. 21 or 25
    child_age_extended_condition: FieldWithCitation[Optional[str]]

    # Special conditions
    senior_loading_percent: FieldWithCitation[float]  # e.g. 0.35 for 35%
    senior_age_range: FieldWithCitation[str]  # "70-75 years"
    special_conditions: FieldWithCitation[list[SpecialCondition]]

    # Commercial
    commission_percent: FieldWithCitation[float]  # 0.20
    marketing_fee_percent: FieldWithCitation[float]  # 0.10
    loss_ratio_estimate: FieldWithCitation[float]  # 0.25
    loss_ratio_review_months: FieldWithCitation[int]  # 6

    # Policy conditions
    free_look_period_days: FieldWithCitation[Optional[int]]
    max_policies_per_cif: FieldWithCitation[int]  # 1

    # Sales
    sales_channel: FieldWithCitation[str]
    payment_source: FieldWithCitation[list[str]]  # ["Conventional", "Syariah"]

    # Content
    benefits: FieldWithCitation[list[BenefitItem]]
    add_on_benefits: FieldWithCitation[list[AddOnBenefit]]
    premium_matrix: FieldWithCitation[list[PremiumRow]]
    exclusions: FieldWithCitation[list[str]]

    # Signatures
    effective_date: FieldWithCitation[str]  # date as string for flexibility
    signing_location: FieldWithCitation[str]
    signatories: FieldWithCitation[list[Signatory]]

    # Meta
    document_language: FieldWithCitation[str]  # "id", "en", "id_en"
    document_version: FieldWithCitation[Optional[str]]

# Extraction Request / Response
class ExtractionRequest(BaseModel):
    """Extraction API request."""
    document_id: str
    schema_type: str = "insurance_product"  # pre-built schema key
    custom_schema: Optional[dict] = None  # user-defined JSON schema

class ExtractionFieldResult(BaseModel):
    """Result for a single extraction field."""
    value: Optional[object] = None
    citation: Optional[Citation] = None
    confidence: float = 0.0
    reasoning: Optional[str] = None

class ExtractionResponse(BaseModel):
    """Extraction API response."""
    extraction_id: str
    document_id: str
    status: str
    result: Optional[dict[str, ExtractionFieldResult]] = None
    error_message: Optional[str] = None

# Pre-built Schemas Registry
PREBUILT_SCHEMAS = {
    "insurance_product": InsuranceProductExtraction,
    # Phase 2: policy_wording, claim_form
}
