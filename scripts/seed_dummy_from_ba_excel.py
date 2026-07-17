#!/usr/bin/env python3
"""Seed DATA HM + STATUS + PO dari workbook BA Monitoring (dummy test, pandas-fast)."""

from __future__ import annotations

import sys
from datetime import datetime, time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import DataHmRow, PoUnitRow, StatusRow  # noqa: E402
from app.routers.hm import _apply_computed  # noqa: E402

DEFAULT_XLSX = Path.home() / "Documents" / "02. BA MONITORING HM PIK JUNI 2026 FINAL.xlsm"


def _to_time(v) -> time | None:
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return None
    if isinstance(v, time):
        return v
    if isinstance(v, datetime):
        return v.time()
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime().time()
    if isinstance(v, (int, float)):
        total = int(round(float(v) * 24 * 3600)) % (24 * 3600)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return time(h, m, s)
    s = str(v).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None


def _to_float(v, default=0.0) -> float:
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def import_data_hm(db, path: Path, limit: int | None = None) -> int:
    """Import seluruh DATA HM dari BA Monitoring (default: tanpa potong baris)."""
    print(f"[1/4] Reading DATA HM (limit={limit or 'ALL'}) …", flush=True)
    df = pd.read_excel(path, sheet_name="DATA HM", header=1, engine="openpyxl")
    df = _norm_cols(df)
    # Drop empty unit/date
    if "CODE UNIT" not in df.columns or "DATE" not in df.columns:
        raise SystemExit(f"DATA HM columns missing: {list(df.columns)[:20]}")
    df = df.dropna(subset=["CODE UNIT", "DATE"])
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"])
    df["SHIFT"] = df.get("SHIFT", "Shift 1").astype(str).str.strip()
    df["VENDOR"] = df.get("VENDOR", "PT. PIK").astype(str).str.strip()
    df["CODE UNIT"] = df["CODE UNIT"].astype(str).str.strip()
    df = df.drop_duplicates(subset=["DATE", "SHIFT", "CODE UNIT"], keep="first")
    if limit is not None and limit > 0:
        df = df.head(limit)

    db.rollback()
    db.query(DataHmRow).delete()
    db.commit()

    n = 0
    for _, r in df.iterrows():
        db.add(DataHmRow(
            date=r["DATE"].date(),
            shift=r["SHIFT"],
            vendor=r["VENDOR"],
            code_unit=r["CODE UNIT"],
            hm_start=_to_float(r.get("HM START")),
            hm_stop=_to_float(r.get("HM STOP")),
            hours_start=_to_time(r.get("HOURS START")),
            hours_stop=_to_time(r.get("HOURS STOP")),
            jam_bd=_to_float(r.get("JAM BD")),
            jam_standby=_to_float(r.get("JAM STANDBY")),
            ritase=_to_float(r.get("RITASE")),
            fuel=_to_float(r.get("Fuel", r.get("FUEL"))),
            hm_pengisian=_to_float(r.get("HM Pengisian ", r.get("HM Pengisian"))),
            located=str(r["LOCATED"]).strip() if pd.notna(r.get("LOCATED")) and str(r.get("LOCATED")).strip() not in ("", "0") else None,
            job_description=str(r["JOB DESCRIPTION"]).strip() if pd.notna(r.get("JOB DESCRIPTION")) else None,
            operator_name=str(r["OPERATORE NAME"]).strip() if pd.notna(r.get("OPERATORE NAME")) and str(r.get("OPERATORE NAME")).strip() not in ("", "0") else None,
            keterangan=str(r["Keterangan"]).strip() if pd.notna(r.get("Keterangan")) and str(r.get("Keterangan")).strip() not in ("", "0") else None,
            exp_difference=str(r["EXP. DIFFERENCE"]).strip() if pd.notna(r.get("EXP. DIFFERENCE")) and str(r.get("EXP. DIFFERENCE")).strip() else None,
        ))
        n += 1
        if n % 200 == 0:
            db.commit()
            print(f"  … {n}", flush=True)
    db.commit()
    print(f"DATA HM imported: {n}", flush=True)
    return n


def import_status(db, path: Path, limit: int | None = None) -> int:
    print(f"[2/4] Reading STATUS (limit={limit or 'ALL'}) …", flush=True)
    # Workbook BA Monitoring: header STATUS di baris 5 → pandas header=4
    read_kw: dict = {"sheet_name": "STATUS", "header": 4, "engine": "openpyxl"}
    if limit is not None and limit > 0:
        read_kw["nrows"] = limit
    body = pd.read_excel(path, **read_kw)
    body = _norm_cols(body)

    # Map columns
    colmap = {c.upper(): c for c in body.columns}

    def pick(*names):
        for n in names:
            if n.upper() in colmap:
                return colmap[n.upper()]
        return None

    c_date = pick("Date", "DATE")
    c_unit = pick("Code Unit", "CODE UNIT")
    c_cat = pick("Category")
    c_item = pick("Item Category")
    c_jam = pick("Jam", "JAM")
    c_shift = pick("Shift", "SHIFT")
    c_area = pick("Working Area")
    c_rem = pick("Remarks / Keterangan", "Remarks")
    c_lok = pick("Lokasi")

    body = body.dropna(subset=[c_unit])
    body[c_date] = pd.to_datetime(body[c_date], errors="coerce")
    body = body.dropna(subset=[c_date])
    if limit is not None and limit > 0:
        body = body.head(limit)

    db.query(StatusRow).delete()
    db.commit()
    n = 0
    for _, r in body.iterrows():
        db.add(StatusRow(
            date=r[c_date].date(),
            code_unit=str(r[c_unit]).strip(),
            category=str(r[c_cat]).strip() if c_cat and pd.notna(r.get(c_cat)) else None,
            item_category=str(r[c_item]).strip() if c_item and pd.notna(r.get(c_item)) else None,
            jam=_to_float(r.get(c_jam) if c_jam else 0),
            shift=str(r[c_shift]).strip() if c_shift and pd.notna(r.get(c_shift)) else None,
            working_area=str(r[c_area]).strip() if c_area and pd.notna(r.get(c_area)) else None,
            remarks=str(r[c_rem]).strip() if c_rem and pd.notna(r.get(c_rem)) else None,
            lokasi=str(r[c_lok]).strip() if c_lok and pd.notna(r.get(c_lok)) else None,
        ))
        n += 1
        if n % 500 == 0:
            db.commit()
            print(f"  … {n}", flush=True)
    db.commit()
    print(f"STATUS imported: {n}", flush=True)
    return n


def import_po(db, path: Path) -> int:
    print("[3/4] Reading PO Unit …", flush=True)
    try:
        df = pd.read_excel(path, sheet_name="PO Unit", header=None, engine="openpyxl")
    except ValueError:
        print("PO Unit sheet missing — skip", flush=True)
        return 0
    header_idx = None
    for i in range(min(15, len(df))):
        vals = [str(x).upper() for x in df.iloc[i].tolist() if pd.notna(x)]
        joined = " ".join(vals)
        if "CODE UNIT" in joined or "LAST PO" in joined:
            header_idx = i
            break
    if header_idx is None:
        print("PO header not found — skip", flush=True)
        return 0
    headers = [str(x).strip() if pd.notna(x) else f"col{j}" for j, x in enumerate(df.iloc[header_idx])]
    body = df.iloc[header_idx + 1 :].copy()
    body.columns = headers
    body = _norm_cols(body)
    colmap = {c.upper(): c for c in body.columns}

    def pick(*names):
        for n in names:
            if n.upper() in colmap:
                return colmap[n.upper()]
        return None

    c_code = pick("Code Unit", "CODE UNIT")
    if not c_code:
        return 0
    c_vendor = pick("Vendor", "VENDOR")
    c_po = pick("Last PO", "LAST PO", "PO NUMBER")
    c_eq = pick("Unit", "UNIT", "Type", "TYPE")
    c_year = pick("Tahun Unit", "TAHUN UNIT", "YEAR")
    c_per = pick("Periode PO", "PERIODE PO", "PERIODE")

    body = body.dropna(subset=[c_code])
    db.query(PoUnitRow).delete()
    db.commit()
    n = 0
    for _, r in body.iterrows():
        code = str(r[c_code]).strip()
        if not code or code.lower() == "nan":
            continue
        db.add(PoUnitRow(
            vendor=str(r[c_vendor]).strip() if c_vendor and pd.notna(r.get(c_vendor)) else None,
            po_number=str(r[c_po]).strip() if c_po and pd.notna(r.get(c_po)) else None,
            equipment=str(r[c_eq]).strip() if c_eq and pd.notna(r.get(c_eq)) else None,
            year=str(r[c_year]).strip() if c_year and pd.notna(r.get(c_year)) else None,
            code_unit_mcr=code,
            periode_str=str(r[c_per]).strip() if c_per and pd.notna(r.get(c_per)) else None,
        ))
        n += 1
    db.commit()
    print(f"PO Unit imported: {n}", flush=True)
    return n


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    # argv[2]/argv[3]: limit opsional; 0 / all / -1 = tanpa potong
    def _parse_limit(raw: str | None, default: int | None) -> int | None:
        if raw is None:
            return default
        if str(raw).strip().lower() in ("", "all", "none", "0", "-1"):
            return None
        return int(raw)

    hm_limit = _parse_limit(sys.argv[2] if len(sys.argv) > 2 else None, None)
    st_limit = _parse_limit(sys.argv[3] if len(sys.argv) > 3 else None, None)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    print(f"Source: {path}", flush=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        import_data_hm(db, path, limit=hm_limit)
        import_status(db, path, limit=st_limit)
        import_po(db, path)
        print("[4/4] Recomputing DATA HM formulas …", flush=True)
        _apply_computed(db)
        print("DONE — dummy siap diuji di UI / API", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
