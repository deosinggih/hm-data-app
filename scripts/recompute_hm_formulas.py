#!/usr/bin/env python3
"""Recompute DATA HM formulas dengan batching untuk performa optimal."""

import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal, engine, Base
from app.models import DataHmRow, StatusRow
from app.services.hm_row_calc import recompute_dataframe
import pandas as pd


def _row_to_dict(r: DataHmRow) -> dict:
    return {
        "id": r.id,
        "date": r.date,
        "shift": r.shift,
        "vendor": r.vendor,
        "code_unit": r.code_unit,
        "code_unit_lapangan": r.code_unit_lapangan,
        "hm_start": r.hm_start,
        "hm_stop": r.hm_stop,
        "hours_start": r.hours_start,
        "hours_stop": r.hours_stop,
        "jam_bd": r.jam_bd,
        "jam_standby": r.jam_standby,
        "ritase": r.ritase,
        "fuel": r.fuel,
        "hm_pengisian": r.hm_pengisian,
        "located": r.located,
        "job_description": r.job_description,
        "operator_name": r.operator_name,
        "keterangan": r.keterangan,
        "exp_difference": r.exp_difference,
        "queery": r.queery,
        "cn": r.cn,
        "amount_hm": r.amount_hm,
        "amount_ew": r.amount_ew,
        "hm_difference": r.hm_difference,
        "information": r.information,
        "hm_today": r.hm_today,
        "pemotongan_hm": r.pemotongan_hm,
        "pemotongan_serap": r.pemotongan_serap,
        "ewh": r.ewh,
        "stb": r.stb,
        "bd": r.bd,
        "hm_pemotongan_status": r.hm_pemotongan_status,
        "remaks": r.remaks,
    }


def get_status_cache(db) -> dict:
    """Pre-group STATUS data by (date, shift, code_unit) untuk fast lookup."""
    print("  Building STATUS cache...")
    rows = db.query(StatusRow).all()
    cache = {}
    for r in rows:
        key = (r.date, r.shift or "", r.code_unit or "")
        if key not in cache:
            cache[key] = {"working": 0.0, "standby": 0.0, "breakdown": 0.0, "remarks": None}

        cat = (r.category or "").upper()
        if cat == "WORKING":
            cache[key]["working"] += r.jam or 0
        elif cat == "STANDBY":
            cache[key]["standby"] += r.jam or 0
        elif cat == "BREAKDOWN":
            cache[key]["breakdown"] += r.jam or 0

        # Check for UR-Operator Problem
        if r.item_category and "UR-Operator Problem" in r.item_category:
            cache[key]["remarks"] = r.remarks

    print(f"    Cached {len(cache)} unique (date, shift, code_unit) combinations")
    return cache


def recompute_with_batching(db, status_cache: dict, batch_size: int = 500) -> None:
    """Recompute formulas dalam batches dengan status_cache untuk performa."""
    from app.services.hm_row_calc import queery, cn_from_unit, amount_hm, amount_ew, information, pemotongan_hm, pemotongan_serap, _r2

    total = db.query(DataHmRow).count()
    print(f"Recomputing {total} rows dengan batch_size={batch_size}...")

    processed = 0
    for offset in range(0, total, batch_size):
        batch_rows = (
            db.query(DataHmRow)
            .order_by(DataHmRow.code_unit, DataHmRow.date, DataHmRow.shift)
            .offset(offset)
            .limit(batch_size)
            .all()
        )

        if not batch_rows:
            break

        # Process each row
        for i, row in enumerate(batch_rows):
            # Basic computations
            row.queery = queery(row.date, row.shift, row.code_unit)
            row.cn = cn_from_unit(row.code_unit)
            row.amount_hm = amount_hm(row.hm_start, row.hm_stop)
            row.amount_ew = amount_ew(row.hours_start, row.hours_stop)

            # HM DIFFERENCE (look ahead untuk next row)
            if i + 1 < len(batch_rows):
                next_row = batch_rows[i + 1]
                if next_row.code_unit == row.code_unit:
                    gap = _r2(float(next_row.hm_start or 0) - float(row.hm_stop or 0))
                    row.hm_difference = f"{gap:.2f}"
                    diff_val = gap if gap > 0 else 0.0
                else:
                    row.hm_difference = "GANTI UNIT"
                    diff_val = 0.0
            else:
                row.hm_difference = "GANTI UNIT"
                diff_val = 0.0

            row.information = information(diff_val, row.exp_difference)
            row.pemotongan_hm = pemotongan_hm(diff_val, row.exp_difference)
            row.pemotongan_serap = pemotongan_serap(diff_val, row.exp_difference)

            # HM TODAY (look back untuk prev row)
            if i > 0:
                prev_row = batch_rows[i - 1]
                if prev_row.date == row.date and prev_row.code_unit == row.code_unit:
                    a0 = prev_row.amount_hm or 0
                    a1 = row.amount_hm or 0
                    row.hm_today = _r2(float(a0) + float(a1))

            # STATUS lookups dari cache
            key = (row.date, row.shift or "", row.code_unit or "")
            if key in status_cache:
                cached = status_cache[key]
                row.ewh = _r2(cached["working"])
                row.stb = _r2(cached["standby"])
                row.bd = _r2(cached["breakdown"])
                row.remaks = cached["remarks"]
            else:
                row.ewh = 0.0
                row.stb = 0.0
                row.bd = 0.0
                row.remaks = None

        db.commit()
        processed += len(batch_rows)
        pct = (processed / total) * 100
        print(f"  [{processed:>5}/{total}] {pct:>5.1f}%")

    print(f"✅ Recomputed {processed} rows")


def main():
    db = SessionLocal()
    try:
        print("="*80)
        print("RECOMPUTE DATA HM FORMULAS (Optimized)")
        print("="*80)

        Base.metadata.create_all(bind=engine)

        print("\n[1/2] Building STATUS cache...")
        status_cache = get_status_cache(db)

        print("\n[2/2] Recomputing DATA HM formulas...")
        recompute_with_batching(db, status_cache, batch_size=500)

        print("\n" + "="*80)
        print("✅ RECOMPUTE SELESAI")
        print("="*80)

        # Verify sample
        print("\nVerifying sample rows...")
        samples = db.query(DataHmRow).filter_by(vendor="PT. PIK").limit(3).all()
        for row in samples:
            print(f"  {row.date} {row.shift} {row.code_unit}: amount_hm={row.amount_hm}, amount_ew={row.amount_ew}, ewh={row.ewh}, stb={row.stb}, bd={row.bd}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
