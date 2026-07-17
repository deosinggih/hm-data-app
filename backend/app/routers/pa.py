from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DataHmRow, PoUnitRow, StatusRow
from app.schemas import PaSummaryOut
from app.services.data_processor import (
    build_pa_rekap,
    build_vendor_summary,
    process_core_data,
)
from app.services.excel_export import export_pa_excel

router = APIRouter(prefix="/api/pa", tags=["pa"])


def _hm_df(db: Session):
    import pandas as pd

    rows = db.query(DataHmRow).all()
    return pd.DataFrame([{
        "DATE": r.date,
        "SHIFT": r.shift,
        "VENDOR": r.vendor,
        "CODE UNIT": r.code_unit,
        "HM START": r.hm_start,
        "HM STOP": r.hm_stop,
        "AMOUNT (HM)": r.amount_hm if r.amount_hm is not None else (r.hm_stop - r.hm_start),
        "INFORMATION": r.information or "",
    } for r in rows])


def _status_df(db: Session):
    import pandas as pd

    rows = db.query(StatusRow).all()
    return pd.DataFrame([{
        "DATE": r.date,
        "SHIFT": r.shift,
        "CODE UNIT": r.code_unit,
        "JAM": r.jam,
        "ITEM": r.item_category,
        "item_category": r.item_category,
        "category": r.category,
        "jam": r.jam,
        "code_unit": r.code_unit,
        "shift": r.shift,
        "date": r.date,
    } for r in rows])


def _po_df(db: Session):
    import pandas as pd

    rows = db.query(PoUnitRow).all()
    if not rows:
        return None
    return pd.DataFrame([{
        "code_unit_mcr": r.code_unit_mcr,
        "po_number": r.po_number,
        "equipment": r.equipment,
        "year": r.year,
        "periode_str": r.periode_str,
    } for r in rows])


@router.get("/summary", response_model=PaSummaryOut)
def pa_summary(
    vendor: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    hm = _hm_df(db)
    st = _status_df(db)
    if hm.empty:
        return PaSummaryOut(recap=[], vendor_summary=[], kpi={
            "pa_overall": 0, "units": 0, "unit_lt_80": 0, "unit_gt_90": 0,
        })
    if st.empty:
        st = hm[["DATE", "SHIFT", "CODE UNIT"]].copy()
        st["JAM"] = 0
        st["ITEM"] = ""
        st["item_category"] = ""
        st["category"] = ""
        st["jam"] = 0
        st["code_unit"] = st["CODE UNIT"]
        st["shift"] = st["SHIFT"]
        st["date"] = st["DATE"]

    _, _, merged = process_core_data(hm, st)
    if vendor:
        merged = merged[merged["VENDOR"] == vendor]
    if date_from:
        merged = merged[merged["DATE_CLEAN"] >= date_from]
    if date_to:
        merged = merged[merged["DATE_CLEAN"] <= date_to]

    recap = build_pa_rekap(merged, _po_df(db))
    vendor_summary = build_vendor_summary(recap)
    jam = float(recap["JAM_TERSEDIA"].sum()) if len(recap) else 0
    bd = float(recap["BD"].sum()) if len(recap) else 0
    pa_overall = round(((jam - bd) / jam) * 100, 2) if jam else 0
    return PaSummaryOut(
        recap=recap.to_dict(orient="records"),
        vendor_summary=vendor_summary.to_dict(orient="records"),
        kpi={
            "pa_overall": pa_overall,
            "units": len(recap),
            "unit_lt_80": int((recap["PA (%)"] < 80).sum()) if len(recap) else 0,
            "unit_gt_90": int((recap["PA (%)"] > 90).sum()) if len(recap) else 0,
            "total_working": float(recap["WORKING"].sum()) if len(recap) else 0,
            "total_bd": bd,
        },
    )


@router.get("/export")
def export_pa(
    vendor: str | None = None,
    db: Session = Depends(get_db),
):
    summary = pa_summary(vendor=vendor, db=db)
    import pandas as pd

    data = export_pa_excel(
        pd.DataFrame(summary.recap),
        pd.DataFrame(summary.vendor_summary),
    )
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Summary_PA_Unit.xlsx"},
    )