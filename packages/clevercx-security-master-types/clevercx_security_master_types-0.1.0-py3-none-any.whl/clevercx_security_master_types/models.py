"""
clevercx-security-master-types
Auto-generated Python type definitions for CleverCX Security Master database entities

DO NOT EDIT MANUALLY - Generated from PostgreSQL database via sqlacodegen
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
#  ENUMS
# ============================================================

class SecurityTypeEnum(str, Enum):
    """Maps to security_type_enum in PostgreSQL"""
    ETF = "ETF"
    ETN = "ETN"
    ETC = "ETC"
    INDEX = "INDEX"
    MODEL = "MODEL"
    MUTUAL_FUND = "MUTUAL_FUND"


class VersionChangeTypeEnum(str, Enum):
    """Maps to version_change_type in PostgreSQL"""
    CREATED = "CREATED"
    REFERENCE_UPDATE = "REFERENCE_UPDATE"
    METADATA_UPDATE = "METADATA_UPDATE"
    SETTINGS_UPDATE = "SETTINGS_UPDATE"
    BULK_UPDATE = "BULK_UPDATE"
    CORRECTION = "CORRECTION"
    RESTATEMENT = "RESTATEMENT"
    SYSTEM_MIGRATION = "SYSTEM_MIGRATION"


class FactsetJobStatusEnum(str, Enum):
    """Maps to factset_job_status in PostgreSQL"""
    QUEUED = "queued"
    EXECUTING = "executing"
    CREATED = "created"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================
#  CORE ENTITIES
# ============================================================

@dataclass
class Security:
    """
    Core security identity table.
    Maps to: securities
    """
    security_id: int
    internal_id: str
    created_at: datetime
    ticker: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    security_type: Optional[SecurityTypeEnum] = None
    authoritative_data_source_id: Optional[int] = None


@dataclass
class DataSource:
    """
    Master list of data providers.
    Maps to: data_sources
    """
    data_source_id: int
    source_name: str
    source_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    source_type: Optional[str] = None
    description: Optional[str] = None


# ============================================================
#  VERSION TABLES
# ============================================================

@dataclass
class SecurityReferenceVersion:
    """
    Vendor reference data from FactSet and other providers.
    Maps to: security_reference_versions
    """
    reference_version_id: int
    security_id: int
    internal_id: str
    version_number: int
    is_current: bool
    created_at: datetime
    data_frequencies: List[str] = field(default_factory=lambda: ["DAILY"])
    name: Optional[str] = None
    description: Optional[str] = None
    asset_class_primary: Optional[str] = None
    asset_class_secondary: Optional[str] = None
    asset_class_tertiary: Optional[str] = None
    assets_under_management: Optional[Decimal] = None
    domicile_country_code: Optional[str] = None
    primary_exposure_region: Optional[str] = None
    primary_exposure_country: Optional[str] = None
    trading_currency: Optional[str] = None
    base_currency: Optional[str] = None
    primary_listing_exchange: Optional[str] = None
    status: Optional[str] = None
    inception_date: Optional[datetime] = None
    issuer_company: Optional[str] = None
    asset_manager: Optional[str] = None
    security_url: Optional[str] = None
    data_source_id: Optional[int] = None
    source_updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    change_reason: Optional[str] = None


@dataclass
class SecurityMetadataVersion:
    """
    Internal CleverCX metadata.
    Maps to: security_metadata_versions
    """
    metadata_version_id: int
    security_id: int
    internal_id: str
    version_number: int
    is_current: bool
    is_template: bool
    is_company_model: bool
    is_archived: bool
    created_at: datetime
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    pdf_url: Optional[str] = None
    planning_objective: Optional[str] = None
    creator_id: Optional[str] = None
    risk_type: Optional[str] = None
    index_id: Optional[int] = None
    mongo_id: Optional[str] = None
    created_by: Optional[str] = None
    change_reason: Optional[str] = None


@dataclass
class SecuritySettingsVersion:
    """
    Calculation configuration.
    Maps to: security_settings_versions
    """
    settings_version_id: int
    security_id: int
    internal_id: str
    version_number: int
    is_current: bool
    created_at: datetime
    calculation_parameters: Dict[str, Any] = field(default_factory=dict)
    data_frequency: Optional[str] = "DAILY"
    stats_loopback_years: Optional[int] = 5
    statistics_window: Optional[int] = None
    risk_free_rate: Optional[Decimal] = None
    created_by: Optional[str] = None
    change_reason: Optional[str] = None


@dataclass
class SecurityVersion:
    """
    Composite snapshot pointing to all version tables.
    Maps to: security_versions
    """
    security_version_id: int
    security_id: int
    internal_id: str
    version_number: int
    is_current: bool
    reference_version_id: int
    metadata_version_id: int
    settings_version_id: int
    change_type: VersionChangeTypeEnum
    created_at: datetime
    change_summary: Optional[str] = None
    ticker_snapshot: Optional[str] = None
    name_snapshot: Optional[str] = None
    created_by: Optional[str] = None


# ============================================================
#  DATA TABLES
# ============================================================

@dataclass
class SecurityComposition:
    """
    Portfolio structure and benchmarks.
    Maps to: security_composition

    composition_type: STRUCTURE (holdings) or BENCHMARK
    """
    composition_id: int
    settings_version_id: int
    composition_type: str  # 'STRUCTURE' or 'BENCHMARK'
    constituent_internal_id: str
    weight: Decimal
    position: int = 0
    constituent_security_id: Optional[int] = None


@dataclass
class SecurityCalculation:
    """
    Point-in-time calculated metrics.
    Maps to: security_calculations
    """
    calculation_id: int
    security_id: int
    internal_id: str
    calculation_date: datetime
    calculated_at: datetime
    extended_metrics: Dict[str, Any] = field(default_factory=dict)
    settings_version_id: Optional[int] = None
    risk_number: Optional[Decimal] = None
    return_value: Optional[Decimal] = None
    risk_score: Optional[Decimal] = None
    sharpe: Optional[Decimal] = None
    sortino: Optional[Decimal] = None
    standard_deviation: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    cagr: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    alpha: Optional[Decimal] = None
    data_points_used: Optional[int] = None
    calculation_start_date: Optional[datetime] = None
    calculation_end_date: Optional[datetime] = None


@dataclass
class SecurityHistoricalPrice:
    """
    Historical price data.
    Maps to: security_historical_prices
    """
    price_id: int
    internal_id: str
    data_source_id: int
    price_date: datetime
    is_latest: bool
    ingested_at: datetime
    security_id: Optional[int] = None
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    adjusted_close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    turnover_value: Optional[Decimal] = None
    dividend_currency: Optional[str] = None
    currency: Optional[str] = None
    price_type: Optional[str] = None


@dataclass
class SecurityReturn:
    """
    Return data.
    Maps to: security_returns
    """
    return_id: int
    internal_id: str
    data_source_id: int
    return_date: datetime
    return_frequency: str
    return_value_type: str
    ingested_at: datetime
    security_id: Optional[int] = None
    return_value: Optional[Decimal] = None


# ============================================================
#  FACTSET TRACKING
# ============================================================

@dataclass
class FactsetJobTracking:
    """
    Tracks FactSet batch jobs.
    Maps to: factset_job_tracking
    """
    job_id: str
    status: FactsetJobStatusEnum
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
    job_name: Optional[str] = None
    securities_count: Optional[int] = None
    records_retrieved: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class FactsetFailedSecurity:
    """
    Failed security fetches.
    Maps to: factset_failed_securities
    """
    id: int
    failed_at: datetime
    retry_count: int
    resolved: bool
    security_id: Optional[int] = None
    internal_id: Optional[str] = None
    ticker: Optional[str] = None
    security_type: Optional[SecurityTypeEnum] = None
    job_id: Optional[str] = None
    failure_reason: Optional[str] = None
    last_retry_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ============================================================
#  VIEWS (Denormalized)
# ============================================================

@dataclass
class VSecuritiesCurrent:
    """
    Current state of all securities (denormalized view).
    Maps to: v_securities_current
    """
    security_id: int
    internal_id: str
    security_created_at: datetime
    ticker: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    security_type: Optional[str] = None
    authoritative_data_source_id: Optional[int] = None
    data_source_name: Optional[str] = None
    security_version_id: Optional[int] = None
    version_number: Optional[int] = None
    last_change_type: Optional[str] = None
    version_created_at: Optional[datetime] = None
    version_created_by: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    asset_class_primary: Optional[str] = None
    asset_class_secondary: Optional[str] = None
    asset_class_tertiary: Optional[str] = None
    assets_under_management: Optional[Decimal] = None
    domicile_country_code: Optional[str] = None
    primary_exposure_region: Optional[str] = None
    primary_exposure_country: Optional[str] = None
    trading_currency: Optional[str] = None
    base_currency: Optional[str] = None
    primary_listing_exchange: Optional[str] = None
    status: Optional[str] = None
    inception_date: Optional[datetime] = None
    issuer_company: Optional[str] = None
    asset_manager: Optional[str] = None
    security_url: Optional[str] = None
    data_frequencies: Optional[List[str]] = None
    pdf_url: Optional[str] = None
    planning_objective: Optional[str] = None
    creator_id: Optional[str] = None
    is_template: Optional[bool] = None
    is_company_model: Optional[bool] = None
    risk_type: Optional[str] = None
    is_archived: Optional[bool] = None
    mongo_id: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    data_frequency: Optional[str] = None
    stats_loopback_years: Optional[int] = None
    statistics_window: Optional[int] = None
    settings_version_id: Optional[int] = None


@dataclass
class VSecurityVersionHistory:
    """
    Complete version history for audit.
    Maps to: v_security_version_history
    """
    security_id: int
    internal_id: str
    security_version_id: int
    version_number: int
    change_type: str
    is_current: bool
    version_created_at: datetime
    reference_version_id: int
    reference_version: int
    metadata_version_id: int
    metadata_version: int
    settings_version_id: int
    settings_version: int
    ticker: Optional[str] = None
    change_summary: Optional[str] = None
    created_by: Optional[str] = None
    name: Optional[str] = None
    asset_class_primary: Optional[str] = None
    status: Optional[str] = None
    reference_change_reason: Optional[str] = None
    is_archived: Optional[bool] = None
    is_template: Optional[bool] = None
    metadata_change_reason: Optional[str] = None
    data_frequency: Optional[str] = None
    stats_loopback_years: Optional[int] = None
    settings_change_reason: Optional[str] = None
