from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    period_of_report: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    filed_at: Mapped[str] = mapped_column(String(10), nullable=False)
    accession_number: Mapped[str] = mapped_column(String(30), nullable=False)
    total_value: Mapped[float] = mapped_column(Float, default=0)  # 천달러 단위
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    holdings: Mapped[list["Holding"]] = relationship("Holding", back_populates="filing", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("investor_id", "accession_number"),
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filing_id: Mapped[int] = mapped_column(Integer, ForeignKey("filings.id"), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=True)
    cusip: Mapped[str] = mapped_column(String(12), nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    value: Mapped[float] = mapped_column(Float, default=0)  # 천달러 단위
    share_type: Mapped[str] = mapped_column(String(20), default="SH")
    # 변동 정보 (전분기 대비)
    shares_change: Mapped[int] = mapped_column(Integer, default=0)
    value_change: Mapped[float] = mapped_column(Float, default=0)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    # 현재가 (yfinance)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    price_updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    filing: Mapped["Filing"] = relationship("Filing", back_populates="holdings")

    __table_args__ = (
        Index("ix_holdings_filing_cusip", "filing_id", "cusip"),
    )


class CusipTicker(Base):
    """CUSIP → Ticker 매핑 캐시."""
    __tablename__ = "cusip_ticker"

    cusip: Mapped[str] = mapped_column(String(12), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
