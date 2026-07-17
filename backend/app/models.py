from datetime import date, datetime, time

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MasterVendor(Base):
    __tablename__ = "master_vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)


class MasterUnit(Base):
    __tablename__ = "master_units"
    __table_args__ = (UniqueConstraint("vendor", "code_unit", name="uq_vendor_unit"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor: Mapped[str] = mapped_column(String(120), index=True)
    code_unit: Mapped[str] = mapped_column(String(120), index=True)


class DataHmRow(Base):
    """Database inputan setara sheet DATA HM."""

    __tablename__ = "data_hm"
    __table_args__ = (
        UniqueConstraint("date", "shift", "code_unit", name="uq_queery"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    shift: Mapped[str] = mapped_column(String(32))
    vendor: Mapped[str] = mapped_column(String(120), index=True)
    code_unit: Mapped[str] = mapped_column(String(120), index=True)
    code_unit_lapangan: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hm_start: Mapped[float] = mapped_column(Float, default=0)
    hm_stop: Mapped[float] = mapped_column(Float, default=0)
    hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    hours_stop: Mapped[time | None] = mapped_column(Time, nullable=True)
    jam_bd: Mapped[float] = mapped_column(Float, default=0)
    jam_standby: Mapped[float] = mapped_column(Float, default=0)
    ritase: Mapped[float] = mapped_column(Float, default=0)
    fuel: Mapped[float] = mapped_column(Float, default=0)
    hm_pengisian: Mapped[float] = mapped_column(Float, default=0)
    located: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keterangan: Mapped[str | None] = mapped_column(Text, nullable=True)
    exp_difference: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Computed (Excel parity)
    queery: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cn: Mapped[str | None] = mapped_column(String(16), nullable=True)
    amount_hm: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_ew: Mapped[float | None] = mapped_column(Float, nullable=True)
    hm_difference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    information: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hm_today: Mapped[float | None] = mapped_column(Float, nullable=True)
    pemotongan_hm: Mapped[float | None] = mapped_column(Float, nullable=True)
    pemotongan_serap: Mapped[float | None] = mapped_column(Float, nullable=True)
    ewh: Mapped[float | None] = mapped_column(Float, nullable=True)
    stb: Mapped[float | None] = mapped_column(Float, nullable=True)
    bd: Mapped[float | None] = mapped_column(Float, nullable=True)
    hm_pemotongan_status: Mapped[float | None] = mapped_column(Float, nullable=True)
    remaks: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class StatusRow(Base):
    __tablename__ = "status_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    code_unit: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    item_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    awal: Mapped[str | None] = mapped_column(String(64), nullable=True)
    akhir: Mapped[str | None] = mapped_column(String(64), nullable=True)
    jam: Mapped[float] = mapped_column(Float, default=0)
    working_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    working_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    shift: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    equipment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lokasi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    query1: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PoUnitRow(Base):
    __tablename__ = "po_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    po_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    year: Mapped[str | None] = mapped_column(String(32), nullable=True)
    code_unit_mcr: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    periode_str: Mapped[str | None] = mapped_column(String(120), nullable=True)
    no_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)


class BaConfig(Base):
    __tablename__ = "ba_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    no_ba: Mapped[str] = mapped_column(String(120), default="")
    lokasi_ttd: Mapped[str] = mapped_column(String(120), default="Pelapis")
    vendor: Mapped[str] = mapped_column(String(120), default="")
    nama_admin: Mapped[str] = mapped_column(String(120), default="")
    nama_sp: Mapped[str] = mapped_column(String(120), default="")
    nama_pm: Mapped[str] = mapped_column(String(120), default="")
    nama_sig: Mapped[str] = mapped_column(String(120), default="")
    nama_pjo: Mapped[str] = mapped_column(String(120), default="")
    nama_ml: Mapped[str] = mapped_column(String(120), default="")
    nama_dibuat: Mapped[str] = mapped_column(String(120), default="")
    jabatan_dibuat: Mapped[str] = mapped_column(String(120), default="Admin Project")
    nama_diperiksa: Mapped[str] = mapped_column(String(120), default="")
    jabatan_diperiksa: Mapped[str] = mapped_column(String(120), default="Sr. Spv. Project Control")
    nama_diketahui: Mapped[str] = mapped_column(String(120), default="")
    jabatan_diketahui: Mapped[str] = mapped_column(String(120), default="")
    ttd_admin: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_sp: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_pm: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_sig: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_pjo: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_ml: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_dibuat: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_diperiksa: Mapped[str | None] = mapped_column(Text, nullable=True)
    ttd_diketahui: Mapped[str | None] = mapped_column(Text, nullable=True)