
from pathlib import Path
from sqlalchemy import create_engine, Integer, String, Text, Float, ForeignKey, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

# Database path setup
DB_PATH = Path(__file__).parent / "socialdeal_casus.sqlite"
engine = create_engine(f"sqlite:///{DB_PATH}")

# 1. Define Base and Declarative ORM Models
class Base(DeclarativeBase):
    pass

class Stad(Base):
    __tablename__ = 'steden'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(Text, nullable=False)
    land: Mapped[str] = mapped_column(Text, nullable=False)
    regio: Mapped[str | None] = mapped_column(Text)
    
    partners: Mapped[list["Partner"]] = relationship(back_populates="stad")

class Partner(Base):
    __tablename__ = 'partners'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(Text, nullable=False)
    stad_id: Mapped[int] = mapped_column(ForeignKey('steden.id'), nullable=False)
    is_test: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    stad: Mapped["Stad"] = relationship(back_populates="partners")
    deals: Mapped[list["Deal"]] = relationship(back_populates="partner")

class Deal(Base):
    __tablename__ = 'deals'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey('partners.id'), nullable=False)
    titel: Mapped[str] = mapped_column(Text, nullable=False)
    start_datum: Mapped[str] = mapped_column(Text, nullable=False)
    eind_datum: Mapped[str] = mapped_column(Text, nullable=False)
    prijs_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    commissie_pct: Mapped[float] = mapped_column(Float, nullable=False)
    
    partner: Mapped["Partner"] = relationship(back_populates="deals")
    verkopen: Mapped[list["Verkoop"]] = relationship(back_populates="deal")

class Verkoop(Base):
    __tablename__ = 'verkopen'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey('deals.id'), nullable=False)
    aangemaakt_op: Mapped[str] = mapped_column(Text, nullable=False)
    verwerkt_op: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    aantal: Mapped[int] = mapped_column(Integer, nullable=False)
    klantprijs_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    commissie_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    klant_email: Mapped[str] = mapped_column(Text, nullable=False)
    betaalreferentie: Mapped[str] = mapped_column(Text, nullable=False)
    
    deal: Mapped["Deal"] = relationship(back_populates="verkopen")