from typing import Optional
import datetime
import decimal

from sqlalchemy import ARRAY, BigInteger, Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, Sequence, String, Table, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship

class Base(MappedAsDataclass, DeclarativeBase):
    pass


class DataSources(Base):
    __tablename__ = 'data_sources'
    __table_args__ = (
        PrimaryKeyConstraint('data_source_id', name='data_sources_pkey'),
        UniqueConstraint('source_code', name='data_sources_source_code_key'),
        UniqueConstraint('source_name', name='data_sources_source_name_key'),
        {'comment': 'Master list of data providers and sources'}
    )

    data_source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_code: Mapped[str] = mapped_column(String(2), nullable=False, comment='2-character code used as prefix in internal_id (e.g., FS, BX, CX)')
    source_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    securities: Mapped[list['Securities']] = relationship('Securities', back_populates='authoritative_data_source')
    security_historical_prices: Mapped[list['SecurityHistoricalPrices']] = relationship('SecurityHistoricalPrices', back_populates='data_source')
    security_historical_prices_p0: Mapped[list['SecurityHistoricalPricesP0']] = relationship('SecurityHistoricalPricesP0', back_populates='data_source')
    security_historical_prices_p1: Mapped[list['SecurityHistoricalPricesP1']] = relationship('SecurityHistoricalPricesP1', back_populates='data_source')
    security_historical_prices_p2: Mapped[list['SecurityHistoricalPricesP2']] = relationship('SecurityHistoricalPricesP2', back_populates='data_source')
    security_historical_prices_p3: Mapped[list['SecurityHistoricalPricesP3']] = relationship('SecurityHistoricalPricesP3', back_populates='data_source')
    security_historical_prices_p4: Mapped[list['SecurityHistoricalPricesP4']] = relationship('SecurityHistoricalPricesP4', back_populates='data_source')
    security_historical_prices_p5: Mapped[list['SecurityHistoricalPricesP5']] = relationship('SecurityHistoricalPricesP5', back_populates='data_source')
    security_historical_prices_p6: Mapped[list['SecurityHistoricalPricesP6']] = relationship('SecurityHistoricalPricesP6', back_populates='data_source')
    security_historical_prices_p7: Mapped[list['SecurityHistoricalPricesP7']] = relationship('SecurityHistoricalPricesP7', back_populates='data_source')
    security_returns: Mapped[list['SecurityReturns']] = relationship('SecurityReturns', back_populates='data_source')
    security_returns_p0: Mapped[list['SecurityReturnsP0']] = relationship('SecurityReturnsP0', back_populates='data_source')
    security_returns_p1: Mapped[list['SecurityReturnsP1']] = relationship('SecurityReturnsP1', back_populates='data_source')
    security_returns_p2: Mapped[list['SecurityReturnsP2']] = relationship('SecurityReturnsP2', back_populates='data_source')
    security_returns_p3: Mapped[list['SecurityReturnsP3']] = relationship('SecurityReturnsP3', back_populates='data_source')
    security_returns_p4: Mapped[list['SecurityReturnsP4']] = relationship('SecurityReturnsP4', back_populates='data_source')
    security_returns_p5: Mapped[list['SecurityReturnsP5']] = relationship('SecurityReturnsP5', back_populates='data_source')
    security_returns_p6: Mapped[list['SecurityReturnsP6']] = relationship('SecurityReturnsP6', back_populates='data_source')
    security_returns_p7: Mapped[list['SecurityReturnsP7']] = relationship('SecurityReturnsP7', back_populates='data_source')
    security_reference_versions: Mapped[list['SecurityReferenceVersions']] = relationship('SecurityReferenceVersions', back_populates='data_source')


class FactsetJobTracking(Base):
    __tablename__ = 'factset_job_tracking'
    __table_args__ = (
        PrimaryKeyConstraint('job_id', name='factset_job_tracking_pkey'),
        Index('idx_factset_job_tracking_status', 'status'),
        Index('idx_factset_job_tracking_submitted_at', 'submitted_at'),
        {'comment': 'Tracks FactSet Batch Processing API jobs'}
    )

    job_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    status: Mapped[str] = mapped_column(Enum('queued', 'executing', 'created', 'succeeded', 'failed', 'cancelled', name='factset_job_status'), nullable=False, server_default=text("'queued'::factset_job_status"))
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    job_name: Mapped[Optional[str]] = mapped_column(String(500))
    securities_count: Mapped[Optional[int]] = mapped_column(Integer)
    records_retrieved: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    factset_failed_securities: Mapped[list['FactsetFailedSecurities']] = relationship('FactsetFailedSecurities', back_populates='job')


t_v_securities_current = Table(
    'v_securities_current', Base.metadata,
    Column('security_id', Integer),
    Column('internal_id', String(11)),
    Column('ticker', String(50)),
    Column('isin', String(50)),
    Column('cusip', String(50)),
    Column('sedol', String(50)),
    Column('security_type', Enum('ETF', 'ETN', 'ETC', 'INDEX', 'MODEL', 'MUTUAL_FUND', name='security_type_enum')),
    Column('authoritative_data_source_id', Integer),
    Column('data_source_name', String(255)),
    Column('security_version_id', BigInteger),
    Column('version_number', Integer),
    Column('last_change_type', Enum('CREATED', 'REFERENCE_UPDATE', 'METADATA_UPDATE', 'SETTINGS_UPDATE', 'BULK_UPDATE', 'CORRECTION', 'RESTATEMENT', 'SYSTEM_MIGRATION', name='version_change_type')),
    Column('version_created_at', DateTime(True)),
    Column('version_created_by', String(255)),
    Column('name', String(255)),
    Column('description', Text),
    Column('asset_class_primary', String(100)),
    Column('asset_class_secondary', String(100)),
    Column('asset_class_tertiary', String(100)),
    Column('assets_under_management', Numeric),
    Column('domicile_country_code', String(10)),
    Column('primary_exposure_region', String(100)),
    Column('primary_exposure_country', String(100)),
    Column('trading_currency', String(10)),
    Column('base_currency', String(10)),
    Column('primary_listing_exchange', String(50)),
    Column('status', String(50)),
    Column('inception_date', DateTime(True)),
    Column('issuer_company', String(255)),
    Column('asset_manager', String(255)),
    Column('security_url', String(1000)),
    Column('data_frequencies', ARRAY(Text())),
    Column('pdf_url', String(1000)),
    Column('planning_objective', String(255)),
    Column('creator_id', String(255)),
    Column('is_template', Boolean),
    Column('is_company_model', Boolean),
    Column('risk_type', String(100)),
    Column('is_archived', Boolean),
    Column('mongo_id', String(24)),
    Column('custom_attributes', JSONB),
    Column('data_frequency', String(50)),
    Column('stats_loopback_years', Integer),
    Column('statistics_window', Integer),
    Column('settings_version_id', BigInteger),
    Column('security_created_at', DateTime(True)),
    comment='Current state of all securities with latest reference, metadata, and settings'
)


t_v_security_version_history = Table(
    'v_security_version_history', Base.metadata,
    Column('security_id', Integer),
    Column('internal_id', String(11)),
    Column('ticker', String(50)),
    Column('security_version_id', BigInteger),
    Column('version_number', Integer),
    Column('change_type', Enum('CREATED', 'REFERENCE_UPDATE', 'METADATA_UPDATE', 'SETTINGS_UPDATE', 'BULK_UPDATE', 'CORRECTION', 'RESTATEMENT', 'SYSTEM_MIGRATION', name='version_change_type')),
    Column('change_summary', Text),
    Column('is_current', Boolean),
    Column('version_created_at', DateTime(True)),
    Column('created_by', String(255)),
    Column('reference_version_id', BigInteger),
    Column('reference_version', Integer),
    Column('name', String(255)),
    Column('asset_class_primary', String(100)),
    Column('status', String(50)),
    Column('reference_change_reason', Text),
    Column('metadata_version_id', BigInteger),
    Column('metadata_version', Integer),
    Column('is_archived', Boolean),
    Column('is_template', Boolean),
    Column('metadata_change_reason', Text),
    Column('settings_version_id', BigInteger),
    Column('settings_version', Integer),
    Column('data_frequency', String(50)),
    Column('stats_loopback_years', Integer),
    Column('settings_change_reason', Text),
    comment='Complete version history for audit and compliance queries'
)


class Securities(Base):
    __tablename__ = 'securities'
    __table_args__ = (
        ForeignKeyConstraint(['authoritative_data_source_id'], ['data_sources.data_source_id'], name='securities_authoritative_data_source_id_fkey'),
        PrimaryKeyConstraint('security_id', name='securities_pkey'),
        UniqueConstraint('cusip', name='securities_cusip_key'),
        UniqueConstraint('internal_id', name='securities_internal_id_key'),
        UniqueConstraint('isin', name='securities_isin_key'),
        UniqueConstraint('ticker', 'authoritative_data_source_id', name='securities_ticker_authoritative_data_source_id_key'),
        {'comment': 'Identity table for securities. Contains only immutable '
                'identifiers.'}
    )

    security_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), nullable=False, comment='Stable identifier. Format: {source_code}-{8_char_base36_hash}')
    ticker: Mapped[Optional[str]] = mapped_column(String(50))
    isin: Mapped[Optional[str]] = mapped_column(String(50))
    cusip: Mapped[Optional[str]] = mapped_column(String(50))
    sedol: Mapped[Optional[str]] = mapped_column(String(50))
    security_type: Mapped[Optional[str]] = mapped_column(Enum('ETF', 'ETN', 'ETC', 'INDEX', 'MODEL', 'MUTUAL_FUND', name='security_type_enum'))
    authoritative_data_source_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    authoritative_data_source: Mapped[Optional['DataSources']] = relationship('DataSources', back_populates='securities')
    factset_failed_securities: Mapped[list['FactsetFailedSecurities']] = relationship('FactsetFailedSecurities', back_populates='security')
    security_metadata_versions: Mapped[list['SecurityMetadataVersions']] = relationship('SecurityMetadataVersions', back_populates='security')
    security_reference_versions: Mapped[list['SecurityReferenceVersions']] = relationship('SecurityReferenceVersions', back_populates='security')
    security_settings_versions: Mapped[list['SecuritySettingsVersions']] = relationship('SecuritySettingsVersions', back_populates='security')
    security_calculations: Mapped[list['SecurityCalculations']] = relationship('SecurityCalculations', back_populates='security')
    security_composition: Mapped[list['SecurityComposition']] = relationship('SecurityComposition', back_populates='constituent_security')
    security_versions: Mapped[list['SecurityVersions']] = relationship('SecurityVersions', back_populates='security')


class SecurityHistoricalPrices(Base):
    __tablename__ = 'security_historical_prices'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_internal_id_data_source_id_price_key'),
        Index('idx_prices_internal_id_date', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices')


class SecurityHistoricalPricesP0(Base):
    __tablename__ = 'security_historical_prices_p0'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p0_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p0_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p0_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p0')


class SecurityHistoricalPricesP1(Base):
    __tablename__ = 'security_historical_prices_p1'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p1_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p1_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p1_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p1')


class SecurityHistoricalPricesP2(Base):
    __tablename__ = 'security_historical_prices_p2'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p2_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p2_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p2_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p2')


class SecurityHistoricalPricesP3(Base):
    __tablename__ = 'security_historical_prices_p3'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p3_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p3_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p3_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p3')


class SecurityHistoricalPricesP4(Base):
    __tablename__ = 'security_historical_prices_p4'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p4_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p4_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p4_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p4')


class SecurityHistoricalPricesP5(Base):
    __tablename__ = 'security_historical_prices_p5'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p5_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p5_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p5_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p5')


class SecurityHistoricalPricesP6(Base):
    __tablename__ = 'security_historical_prices_p6'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p6_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p6_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p6_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p6')


class SecurityHistoricalPricesP7(Base):
    __tablename__ = 'security_historical_prices_p7'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_historical_prices_data_source_id_fkey'),
        PrimaryKeyConstraint('price_id', 'internal_id', name='security_historical_prices_p7_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'price_date', name='security_historical_prices_p7_internal_id_data_source_id_pr_key'),
        Index('security_historical_prices_p7_internal_id_price_date_idx', 'internal_id', 'price_date')
    )

    price_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_historical_prices_price_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    open_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    high_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    low_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    adjusted_close_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    dividend_currency: Mapped[Optional[str]] = mapped_column(String(10))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    price_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_historical_prices_p7')


class SecurityReturns(Base):
    __tablename__ = 'security_returns'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_internal_id_data_source_id_return_frequenc_key'),
        Index('idx_returns_internal_id_date', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns')


class SecurityReturnsP0(Base):
    __tablename__ = 'security_returns_p0'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p0_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p0_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p0_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p0')


class SecurityReturnsP1(Base):
    __tablename__ = 'security_returns_p1'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p1_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p1_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p1_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p1')


class SecurityReturnsP2(Base):
    __tablename__ = 'security_returns_p2'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p2_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p2_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p2_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p2')


class SecurityReturnsP3(Base):
    __tablename__ = 'security_returns_p3'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p3_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p3_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p3_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p3')


class SecurityReturnsP4(Base):
    __tablename__ = 'security_returns_p4'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p4_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p4_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p4_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p4')


class SecurityReturnsP5(Base):
    __tablename__ = 'security_returns_p5'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p5_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p5_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p5_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p5')


class SecurityReturnsP6(Base):
    __tablename__ = 'security_returns_p6'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p6_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p6_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p6_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p6')


class SecurityReturnsP7(Base):
    __tablename__ = 'security_returns_p7'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_returns_data_source_id_fkey'),
        PrimaryKeyConstraint('return_id', 'internal_id', name='security_returns_p7_pkey'),
        UniqueConstraint('internal_id', 'data_source_id', 'return_frequency', 'return_value_type', 'return_date', name='security_returns_p7_internal_id_data_source_id_return_frequ_key'),
        Index('security_returns_p7_internal_id_return_frequency_return_val_idx', 'internal_id', 'return_frequency', 'return_value_type', 'return_date')
    )

    return_id: Mapped[int] = mapped_column(BigInteger, Sequence('security_returns_return_id_seq'), primary_key=True)
    internal_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    return_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    return_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    return_value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    ingested_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    data_source: Mapped['DataSources'] = relationship('DataSources', back_populates='security_returns_p7')


class FactsetFailedSecurities(Base):
    __tablename__ = 'factset_failed_securities'
    __table_args__ = (
        ForeignKeyConstraint(['job_id'], ['factset_job_tracking.job_id'], name='factset_failed_securities_job_id_fkey'),
        ForeignKeyConstraint(['security_id'], ['securities.security_id'], name='factset_failed_securities_security_id_fkey'),
        PrimaryKeyConstraint('id', name='factset_failed_securities_pkey'),
        Index('idx_factset_failed_securities_resolved', 'resolved'),
        Index('idx_factset_failed_securities_security_id', 'security_id'),
        {'comment': 'Tracks securities that failed during FactSet data fetching'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    security_id: Mapped[Optional[int]] = mapped_column(Integer)
    internal_id: Mapped[Optional[str]] = mapped_column(String(11))
    ticker: Mapped[Optional[str]] = mapped_column(String(50))
    security_type: Mapped[Optional[str]] = mapped_column(Enum('ETF', 'ETN', 'ETC', 'INDEX', 'MODEL', 'MUTUAL_FUND', name='security_type_enum'))
    job_id: Mapped[Optional[str]] = mapped_column(String(255))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    failed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    last_retry_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    resolved: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    job: Mapped[Optional['FactsetJobTracking']] = relationship('FactsetJobTracking', back_populates='factset_failed_securities')
    security: Mapped[Optional['Securities']] = relationship('Securities', back_populates='factset_failed_securities')


class SecurityMetadataVersions(Base):
    __tablename__ = 'security_metadata_versions'
    __table_args__ = (
        ForeignKeyConstraint(['security_id'], ['securities.security_id'], ondelete='CASCADE', name='security_metadata_versions_security_id_fkey'),
        PrimaryKeyConstraint('metadata_version_id', name='security_metadata_versions_pkey'),
        UniqueConstraint('security_id', 'version_number', name='security_metadata_versions_security_id_version_number_key'),
        Index('idx_metadata_current_version', 'security_id', unique=True),
        Index('idx_metadata_versions_archived', 'is_archived'),
        Index('idx_metadata_versions_internal_id', 'internal_id'),
        Index('idx_metadata_versions_mongo_id', 'mongo_id'),
        Index('idx_metadata_versions_security_id', 'security_id', 'version_number'),
        {'comment': 'Versioned internal metadata defined by CleverCX'}
    )

    metadata_version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    security_id: Mapped[int] = mapped_column(Integer, nullable=False)
    internal_id: Mapped[str] = mapped_column(String(11), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    pdf_url: Mapped[Optional[str]] = mapped_column(String(1000))
    planning_objective: Mapped[Optional[str]] = mapped_column(String(255))
    creator_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_template: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    is_company_model: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    risk_type: Mapped[Optional[str]] = mapped_column(String(100))
    is_archived: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    index_id: Mapped[Optional[int]] = mapped_column(Integer)
    mongo_id: Mapped[Optional[str]] = mapped_column(String(24))
    custom_attributes: Mapped[Optional[dict]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    change_reason: Mapped[Optional[str]] = mapped_column(Text)

    security: Mapped['Securities'] = relationship('Securities', back_populates='security_metadata_versions')
    security_versions: Mapped[list['SecurityVersions']] = relationship('SecurityVersions', back_populates='metadata_version')


class SecurityReferenceVersions(Base):
    __tablename__ = 'security_reference_versions'
    __table_args__ = (
        ForeignKeyConstraint(['data_source_id'], ['data_sources.data_source_id'], name='security_reference_versions_data_source_id_fkey'),
        ForeignKeyConstraint(['security_id'], ['securities.security_id'], ondelete='CASCADE', name='security_reference_versions_security_id_fkey'),
        PrimaryKeyConstraint('reference_version_id', name='security_reference_versions_pkey'),
        UniqueConstraint('security_id', 'version_number', name='security_reference_versions_security_id_version_number_key'),
        Index('idx_reference_current_version', 'security_id', unique=True),
        Index('idx_reference_versions_internal_id', 'internal_id'),
        Index('idx_reference_versions_name', 'name'),
        Index('idx_reference_versions_security_id', 'security_id', 'version_number'),
        {'comment': 'Versioned reference data from FactSet and other vendors'}
    )

    reference_version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    security_id: Mapped[int] = mapped_column(Integer, nullable=False)
    internal_id: Mapped[str] = mapped_column(String(11), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    asset_class_primary: Mapped[Optional[str]] = mapped_column(String(100))
    asset_class_secondary: Mapped[Optional[str]] = mapped_column(String(100))
    asset_class_tertiary: Mapped[Optional[str]] = mapped_column(String(100))
    assets_under_management: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    domicile_country_code: Mapped[Optional[str]] = mapped_column(String(10))
    primary_exposure_region: Mapped[Optional[str]] = mapped_column(String(100))
    primary_exposure_country: Mapped[Optional[str]] = mapped_column(String(100))
    trading_currency: Mapped[Optional[str]] = mapped_column(String(10))
    base_currency: Mapped[Optional[str]] = mapped_column(String(10))
    primary_listing_exchange: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    inception_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    issuer_company: Mapped[Optional[str]] = mapped_column(String(255))
    asset_manager: Mapped[Optional[str]] = mapped_column(String(255))
    security_url: Mapped[Optional[str]] = mapped_column(String(1000))
    data_frequencies: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()), server_default=text("ARRAY['DAILY'::text]"))
    data_source_id: Mapped[Optional[int]] = mapped_column(Integer)
    source_updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    change_reason: Mapped[Optional[str]] = mapped_column(Text)

    data_source: Mapped[Optional['DataSources']] = relationship('DataSources', back_populates='security_reference_versions')
    security: Mapped['Securities'] = relationship('Securities', back_populates='security_reference_versions')
    security_versions: Mapped[list['SecurityVersions']] = relationship('SecurityVersions', back_populates='reference_version')


class SecuritySettingsVersions(Base):
    __tablename__ = 'security_settings_versions'
    __table_args__ = (
        ForeignKeyConstraint(['security_id'], ['securities.security_id'], ondelete='CASCADE', name='security_settings_versions_security_id_fkey'),
        PrimaryKeyConstraint('settings_version_id', name='security_settings_versions_pkey'),
        UniqueConstraint('security_id', 'version_number', name='security_settings_versions_security_id_version_number_key'),
        Index('idx_settings_current_version', 'security_id', unique=True),
        Index('idx_settings_versions_internal_id', 'internal_id'),
        Index('idx_settings_versions_security_id', 'security_id', 'version_number'),
        {'comment': 'Versioned calculation settings'}
    )

    settings_version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    security_id: Mapped[int] = mapped_column(Integer, nullable=False)
    internal_id: Mapped[str] = mapped_column(String(11), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    data_frequency: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("'DAILY'::character varying"))
    stats_loopback_years: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('5'))
    statistics_window: Mapped[Optional[int]] = mapped_column(Integer)
    risk_free_rate: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(8, 6), server_default=text('0.01'))
    calculation_parameters: Mapped[Optional[dict]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    change_reason: Mapped[Optional[str]] = mapped_column(Text)

    security: Mapped['Securities'] = relationship('Securities', back_populates='security_settings_versions')
    security_calculations: Mapped[list['SecurityCalculations']] = relationship('SecurityCalculations', back_populates='settings_version')
    security_composition: Mapped[list['SecurityComposition']] = relationship('SecurityComposition', back_populates='settings_version')
    security_versions: Mapped[list['SecurityVersions']] = relationship('SecurityVersions', back_populates='settings_version')


class SecurityCalculations(Base):
    __tablename__ = 'security_calculations'
    __table_args__ = (
        ForeignKeyConstraint(['security_id'], ['securities.security_id'], ondelete='CASCADE', name='security_calculations_security_id_fkey'),
        ForeignKeyConstraint(['settings_version_id'], ['security_settings_versions.settings_version_id'], name='security_calculations_settings_version_id_fkey'),
        PrimaryKeyConstraint('calculation_id', name='security_calculations_pkey'),
        UniqueConstraint('security_id', 'calculation_date', 'settings_version_id', name='security_calculations_security_id_calculation_date_settings_key'),
        Index('idx_calculations_internal_id', 'internal_id', 'calculation_date'),
        Index('idx_calculations_security_date', 'security_id', 'calculation_date'),
        Index('idx_calculations_settings', 'settings_version_id')
    )

    calculation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    security_id: Mapped[int] = mapped_column(Integer, nullable=False)
    internal_id: Mapped[str] = mapped_column(String(11), nullable=False)
    calculation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    settings_version_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    calculated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    risk_number: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 4))
    return_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 6))
    risk_score: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 4))
    sharpe: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 4))
    sortino: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 4))
    standard_deviation: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 6))
    max_drawdown: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 6))
    cagr: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 6))
    beta: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 4))
    alpha: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 6))
    extended_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    data_points_used: Mapped[Optional[int]] = mapped_column(Integer)
    calculation_start_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    calculation_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    security: Mapped['Securities'] = relationship('Securities', back_populates='security_calculations')
    settings_version: Mapped[Optional['SecuritySettingsVersions']] = relationship('SecuritySettingsVersions', back_populates='security_calculations')


class SecurityComposition(Base):
    __tablename__ = 'security_composition'
    __table_args__ = (
        CheckConstraint("composition_type::text = ANY (ARRAY['STRUCTURE'::character varying, 'BENCHMARK'::character varying]::text[])", name='security_composition_composition_type_check'),
        CheckConstraint('weight > 0::numeric AND weight <= 1::numeric', name='valid_weight'),
        ForeignKeyConstraint(['constituent_security_id'], ['securities.security_id'], name='security_composition_constituent_security_id_fkey'),
        ForeignKeyConstraint(['settings_version_id'], ['security_settings_versions.settings_version_id'], ondelete='CASCADE', name='security_composition_settings_version_id_fkey'),
        PrimaryKeyConstraint('composition_id', name='security_composition_pkey'),
        UniqueConstraint('settings_version_id', 'composition_type', 'constituent_internal_id', name='security_composition_settings_version_id_composition_type_c_key'),
        Index('idx_composition_constituent', 'constituent_security_id'),
        Index('idx_composition_internal_id', 'constituent_internal_id'),
        Index('idx_composition_settings', 'settings_version_id'),
        Index('idx_composition_type', 'settings_version_id', 'composition_type'),
        {'comment': 'Portfolio composition and benchmarks. Versioned via '
                'settings_version_id.'}
    )

    composition_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    settings_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    composition_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='STRUCTURE = portfolio holdings, BENCHMARK = benchmark allocation')
    constituent_internal_id: Mapped[str] = mapped_column(String(11), nullable=False, comment='Internal ID of constituent security. Immutable identifier.')
    weight: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    constituent_security_id: Mapped[Optional[int]] = mapped_column(Integer)

    constituent_security: Mapped[Optional['Securities']] = relationship('Securities', back_populates='security_composition')
    settings_version: Mapped['SecuritySettingsVersions'] = relationship('SecuritySettingsVersions', back_populates='security_composition')


class SecurityVersions(Base):
    __tablename__ = 'security_versions'
    __table_args__ = (
        ForeignKeyConstraint(['metadata_version_id'], ['security_metadata_versions.metadata_version_id'], name='security_versions_metadata_version_id_fkey'),
        ForeignKeyConstraint(['reference_version_id'], ['security_reference_versions.reference_version_id'], name='security_versions_reference_version_id_fkey'),
        ForeignKeyConstraint(['security_id'], ['securities.security_id'], ondelete='CASCADE', name='security_versions_security_id_fkey'),
        ForeignKeyConstraint(['settings_version_id'], ['security_settings_versions.settings_version_id'], name='security_versions_settings_version_id_fkey'),
        PrimaryKeyConstraint('security_version_id', name='security_versions_pkey'),
        UniqueConstraint('security_id', 'version_number', name='security_versions_security_id_version_number_key'),
        Index('idx_security_versions_created_at', 'created_at'),
        Index('idx_security_versions_current', 'security_id', unique=True),
        Index('idx_security_versions_internal_id', 'internal_id', 'version_number'),
        Index('idx_security_versions_security_id', 'security_id', 'version_number'),
        {'comment': 'Composite version snapshots. This is what Proposals reference.'}
    )

    security_version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    security_id: Mapped[int] = mapped_column(Integer, nullable=False)
    internal_id: Mapped[str] = mapped_column(String(11), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metadata_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    settings_version_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    change_type: Mapped[str] = mapped_column(Enum('CREATED', 'REFERENCE_UPDATE', 'METADATA_UPDATE', 'SETTINGS_UPDATE', 'BULK_UPDATE', 'CORRECTION', 'RESTATEMENT', 'SYSTEM_MIGRATION', name='version_change_type'), nullable=False, server_default=text("'CREATED'::version_change_type"))
    is_current: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    ticker_snapshot: Mapped[Optional[str]] = mapped_column(String(50))
    name_snapshot: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

    metadata_version: Mapped['SecurityMetadataVersions'] = relationship('SecurityMetadataVersions', back_populates='security_versions')
    reference_version: Mapped['SecurityReferenceVersions'] = relationship('SecurityReferenceVersions', back_populates='security_versions')
    security: Mapped['Securities'] = relationship('Securities', back_populates='security_versions')
    settings_version: Mapped['SecuritySettingsVersions'] = relationship('SecuritySettingsVersions', back_populates='security_versions')
