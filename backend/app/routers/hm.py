from datetime import date, time

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DataHmRow, StatusRow
from app.schemas import HmRowIn, HmRowOut, ImportResult, SuggestHmStartOut
from app.services.excel_import import import_data_hm_excel
from app.services.hm_row_calc import recompute_dataframe, validate_row

router = APIRouter(prefix="/api/hm", tags=["hm"])


def _status_df(db: Session):
    import pandas as pd

    rows = db.query(StatusRow).all()
    if not rows:
        return None
    return pd.DataFrame([{
        "date": r.date,
        "code_unit": r.code_unit,
        "category": r.category,
        "item_category": r.item_category,
        "jam": r.jam,
        "shift": r.shift,
        "remarks": r.remarks,
    } for r in rows])


def _r2(v):
    if v is None:
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return v


def _row_to_dict(r: DataHmRow) -> dict:
    return {
        "id": r.id,
        "date": r.date,
        "shift": r.shift,
        "vendor": r.vendor,
        "code_unit": r.code_unit,
        "code_unit_lapangan": r.code_unit_lapangan,
        "hm_start": _r2(r.hm_start),
        "hm_stop": _r2(r.hm_stop),
        "hours_start": r.hours_start,
        "hours_stop": r.hours_stop,
        "jam_bd": _r2(r.jam_bd),
        "jam_standby": _r2(r.jam_standby),
        "ritase": r.ritase,
        "fuel": _r2(r.fuel),
        "hm_pengisian": _r2(r.hm_pengisian),
        "located": r.located,
        "job_description": r.job_description,
        "operator_name": r.operator_name,
        "keterangan": r.keterangan,
        "exp_difference": r.exp_difference,
        "queery": r.queery,
        "cn": r.cn,
        "amount_hm": _r2(r.amount_hm),
        "amount_ew": _r2(r.amount_ew),
        "hm_difference": r.hm_difference,
        "information": r.information,
        "hm_today": _r2(r.hm_today),
        "pemotongan_hm": _r2(r.pemotongan_hm),
        "pemotongan_serap": _r2(r.pemotongan_serap),
        "ewh": _r2(r.ewh),
        "stb": _r2(r.stb),
        "bd": _r2(r.bd),
        "hm_pemotongan_status": _r2(r.hm_pemotongan_status),
        "remaks": r.remaks,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }


def _apply_computed(db: Session) -> None:
    rows = db.query(DataHmRow).all()
    if not rows:
        return
    dicts = [_row_to_dict(r) for r in rows]
    computed = recompute_dataframe(dicts, _status_df(db))
    by_id = {c["id"]: c for c in computed}
    for r in rows:
        c = by_id.get(r.id)
        if not c:
            continue
        for field in (
            "queery", "cn", "amount_hm", "amount_ew", "hm_difference",
            "information", "hm_today", "pemotongan_hm", "pemotongan_serap",
            "ewh", "stb", "bd", "hm_pemotongan_status", "remaks",
        ):
            setattr(r, field, c.get(field))
    db.commit()


def _default_hours(shift: str) -> tuple[time, time]:
    s = str(shift).lower()
    if "2" in s:
        return time(18, 0), time(6, 0)
    return time(6, 0), time(18, 0)


@router.get("", response_model=list[HmRowOut])
def list_hm(
    vendor: str | None = None,
    code_unit: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(DataHmRow)
    if vendor:
        q = q.filter(DataHmRow.vendor == vendor)
    if code_unit:
        q = q.filter(DataHmRow.code_unit == code_unit)
    if date_from:
        q = q.filter(DataHmRow.date >= date_from)
    if date_to:
        q = q.filter(DataHmRow.date <= date_to)
    # Sort: DATE → CODE UNIT → SHIFT → HM START (sequential HM start untuk multiple operators same shift)
    rows = q.order_by(
        DataHmRow.date.asc(),
        DataHmRow.code_unit.asc(),
        DataHmRow.shift.asc(),
        DataHmRow.hm_start.asc(),
    ).all()
    return rows


@router.get("/suggest-start", response_model=SuggestHmStartOut)
def suggest_start(
    code_unit: str = Query(...),
    date_: date = Query(alias="date"),
    shift: str = Query(...),
    db: Session = Depends(get_db),
):
    prev = (
        db.query(DataHmRow)
        .filter(DataHmRow.code_unit == code_unit)
        .order_by(DataHmRow.date.desc(), DataHmRow.shift.desc())
        .first()
    )
    if not prev:
        return SuggestHmStartOut(hm_start=None, message="Belum ada histori unit")
    return SuggestHmStartOut(
        hm_start=prev.hm_stop,
        message=f"Dari HM STOP sebelumnya ({prev.date} {prev.shift})",
    )


@router.post("", response_model=HmRowOut)
def create_hm(payload: HmRowIn, db: Session = Depends(get_db)):
    data = payload.model_dump()
    errors = validate_row(data)
    if errors:
        raise HTTPException(400, detail="; ".join(errors))

    exists = (
        db.query(DataHmRow)
        .filter_by(date=payload.date, shift=payload.shift, code_unit=payload.code_unit)
        .first()
    )
    if exists:
        raise HTTPException(400, detail="Duplikat QUEERY (DATE+SHIFT+CODE UNIT)")

    hs, he = payload.hours_start, payload.hours_stop
    if hs is None or he is None:
        dhs, dhe = _default_hours(payload.shift)
        hs = hs or dhs
        he = he or dhe

    row = DataHmRow(
        date=payload.date,
        shift=payload.shift,
        vendor=payload.vendor,
        code_unit=payload.code_unit,
        code_unit_lapangan=payload.code_unit_lapangan,
        hm_start=payload.hm_start,
        hm_stop=payload.hm_stop,
        hours_start=hs,
        hours_stop=he,
        jam_bd=payload.jam_bd,
        jam_standby=payload.jam_standby,
        ritase=payload.ritase,
        fuel=payload.fuel,
        hm_pengisian=payload.hm_pengisian,
        located=payload.located,
        job_description=payload.job_description,
        operator_name=payload.operator_name,
        keterangan=payload.keterangan,
        exp_difference=payload.exp_difference,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    _apply_computed(db)
    db.refresh(row)
    return row


@router.put("/{row_id}", response_model=HmRowOut)
def update_hm(row_id: int, payload: HmRowIn, db: Session = Depends(get_db)):
    row = db.query(DataHmRow).filter_by(id=row_id).first()
    if not row:
        raise HTTPException(404, detail="Row not found")
    errors = validate_row(payload.model_dump())
    if errors:
        raise HTTPException(400, detail="; ".join(errors))
    dup = (
        db.query(DataHmRow)
        .filter(
            DataHmRow.date == payload.date,
            DataHmRow.shift == payload.shift,
            DataHmRow.code_unit == payload.code_unit,
            DataHmRow.id != row_id,
        )
        .first()
    )
    if dup:
        raise HTTPException(400, detail="Duplikat QUEERY (DATE+SHIFT+CODE UNIT)")

    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    _apply_computed(db)
    db.refresh(row)
    return row


@router.delete("/{row_id}")
def delete_hm(row_id: int, db: Session = Depends(get_db)):
    row = db.query(DataHmRow).filter_by(id=row_id).first()
    if not row:
        raise HTTPException(404, detail="Row not found")
    db.delete(row)
    db.commit()
    _apply_computed(db)
    return {"ok": True}


@router.post("/recompute")
def recompute(db: Session = Depends(get_db)):
    _apply_computed(db)
    return {"ok": True, "message": "Recomputed all DATA HM formulas"}


@router.post("/import", response_model=ImportResult)
async def import_hm(
    file: UploadFile = File(...),
    replace: bool = True,
    db: Session = Depends(get_db),
):
    """Browse/upload Excel yang berisi sheet DATA HM."""
    content = await file.read()
    if not content:
        raise HTTPException(400, detail="File kosong")
    try:
        n = import_data_hm_excel(db, content, replace=replace)
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(400, detail=f"Gagal baca Excel: {e}") from e
    _apply_computed(db)
    return ImportResult(
        sheet="DATA HM",
        rows=n,
        message=f"Imported {n} baris dari sheet DATA HM",
    )