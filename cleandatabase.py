
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Database path setup
DB_PATH = Path(__file__).parent / "socialdeal_clean.sqlite"
engine = create_engine(f"sqlite:///{DB_PATH}")

# 1. Define Base and Declarative ORM Models
class Base(DeclarativeBase):
    pass


# The clean tables have no SQLite foreign-key constraints; these declarations
# describe the logical joins for SQLAlchemy relationships.
class Stad(Base):
    __tablename__ = "clean_steden"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(Text, nullable=False)
    land: Mapped[str] = mapped_column(Text, nullable=False)
    regio: Mapped[str | None] = mapped_column(Text)

    partners: Mapped[list[Partner]] = relationship(back_populates="stad")


class Partner(Base):
    __tablename__ = "clean_partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(Text, nullable=False)
    stad_id: Mapped[int] = mapped_column(
        ForeignKey("clean_steden.id"), nullable=False
    )
    is_test: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    stad: Mapped["Stad"] = relationship(back_populates="partners")
    deals: Mapped[list["Deal"]] = relationship(back_populates="partner")


class Deal(Base):
    __tablename__ = "clean_deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("clean_partners.id"), nullable=False
    )
    titel: Mapped[str] = mapped_column(Text, nullable=False)
    start_datum: Mapped[str] = mapped_column(Text, nullable=False)
    eind_datum: Mapped[str] = mapped_column(Text, nullable=False)
    prijs_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    commissie_pct: Mapped[float] = mapped_column(Float, nullable=False)
    partner_is_test: Mapped[int] = mapped_column(Integer, nullable=False)

    partner: Mapped[Partner] = relationship(back_populates="deals")
    verkopen: Mapped[list[Verkoop]] = relationship(back_populates="deal")


class Verkoop(Base):
    __tablename__ = "clean_verkopen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("clean_deals.id"), nullable=False)
    aangemaakt_op: Mapped[str] = mapped_column(Text, nullable=False)
    verwerkt_op: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    aantal: Mapped[int] = mapped_column(Integer, nullable=False)
    klantprijs_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    commissie_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    klant_id: Mapped[str] = mapped_column(Text, nullable=False)
    status_clean: Mapped[str] = mapped_column(Text, nullable=False)
    partner_is_test: Mapped[int] = mapped_column(Integer, nullable=False)
    telt_mee_voor_omzet: Mapped[int] = mapped_column(Integer, nullable=False)
    aangemaakt_op_nl: Mapped[str] = mapped_column(Text, nullable=False)
    verwerkt_op_nl: Mapped[str] = mapped_column(Text, nullable=False)

    deal: Mapped[Deal] = relationship(back_populates="verkopen")


class DqLog(Base):
    __tablename__ = "dq_log"

    description: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_tz: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    # dq_log has no declared primary key; descriptions are unique per build.
    __mapper_args__ = {"primary_key": [description]}
    