from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional

from pydantic import BaseModel, Field


class MasterUnitOut(BaseModel):
    id: int
    vendor: str
    code_unit: str

    model_config = {"from_attributes": True}


class VendorUnitsOut(BaseModel):
    vendors: list[str]
    units_by_vendor: dict[str, list[str]]


class HmRowIn(BaseModel):
    date: date
    shift: str
    vendor: str
    code_unit: str
    code_unit_lapangan: str | None = None
    hm_start: float = 0
    hm_stop: float = 0
    hours_start: time | None = None
    hours_stop: time | None = None
    jam_bd: float = 0
    jam_standby: float = 0
    ritase: float = 0
    fuel: float = 0
    hm_pengisian: float = 0
    located: str | None = None
    job_description: str | None = None
    operator_name: str | None = None
    keterangan: str | None = None
    exp_difference: str | None = None


class HmRowOut(HmRowIn):
    id: int
    queery: str | None = None
    cn: str | None = None
    amount_hm: float | None = None
    amount_ew: float | None = None
    hm_difference: str | None = None
    information: str | None = None
    hm_today: float | None = None
    pemotongan_hm: float | None = None
    pemotongan_serap: float | None = None
    ewh: float | None = None
    stb: float | None = None
    bd: float | None = None
    hm_pemotongan_status: float | None = None
    remaks: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StatusRowOut(BaseModel):
    id: int
    date: Optional[date] = None
    code_unit: Optional[str] = None
    category: Optional[str] = None
    item_category: Optional[str] = None
    jam: float = 0
    shift: Optional[str] = None
    working_area: Optional[str] = None
    remarks: Optional[str] = None
    lokasi: Optional[str] = None

    model_config = {"from_attributes": True}


class ImportResult(BaseModel):
    sheet: str
    rows: int
    message: str


class BaConfigIn(BaseModel):
    no_ba: str = ""
    lokasi_ttd: str = "Pelapis"
    vendor: str = ""
    nama_admin: str = ""
    nama_sp: str = ""
    nama_pm: str = ""
    nama_sig: str = ""
    nama_pjo: str = ""
    nama_ml: str = ""
    nama_dibuat: str = ""
    jabatan_dibuat: str = "Admin Project"
    nama_diperiksa: str = ""
    jabatan_diperiksa: str = "Sr. Spv. Project Control"
    nama_diketahui: str = ""
    jabatan_diketahui: str = ""


class BaConfigOut(BaConfigIn):
    id: int
    has_ttd_admin: bool = False
    has_ttd_sp: bool = False
    has_ttd_pm: bool = False
    has_ttd_sig: bool = False
    has_ttd_pjo: bool = False
    has_ttd_ml: bool = False
    has_ttd_dibuat: bool = False
    has_ttd_diperiksa: bool = False
    has_ttd_diketahui: bool = False

    model_config = {"from_attributes": True}


class PaUnitRow(BaseModel):
    vendor: str
    code_unit: str
    pa_percent: float = Field(alias="PA (%)")
    jam_tersedia: float
    working: float
    bd: float
    fm: float
    stby: float
    pot_z: float
    total_shift: int
    po_number: str | None = None
    equipment: str | None = None
    year: str | None = None
    periode_str: str | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class PaSummaryOut(BaseModel):
    recap: list[dict[str, Any]]
    vendor_summary: list[dict[str, Any]]
    kpi: dict[str, Any]


class BaPreviewOut(BaseModel):
    vendor: str
    title: str
    no_ba: str
    narasi: str
    rows: list[dict[str, Any]]
    tanggal_ttd: str
    company_name: str = "PT. Kayong Aluminium Nusantara"
    company_address_line1: str = ""
    company_address_line2: str = ""
    columns: list[str] = []


class SuggestHmStartOut(BaseModel):
    hm_start: float | None
    message: str