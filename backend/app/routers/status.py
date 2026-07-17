from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StatusRow
from app.schemas import ImportResult, StatusRowOut
from app.services.excel_export import export_status_browse_xlsx
from app.services.excel_import import import_status_excel

router = APIRouter(prefix="/api/status", tags=["status"])


@router.post("/import", response_model=ImportResult)
async def import_status(
    file: UploadFile = File(...),
    replace: bool = True,
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        n = import_status_excel(db, content, replace=replace)
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    return ImportResult(sheet="STATUS", rows=n, message=f"Imported {n} STATUS rows")


@router.get("", response_model=list[StatusRowOut])
def browse_status(
    vendor_unit: str | None = None,
    code_unit: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = Query(None, description="search remarks/item"),
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db),
):
    query = db.query(StatusRow)
    if code_unit or vendor_unit:
        query = query.filter(StatusRow.code_unit == (code_unit or vendor_unit))
    if category:
        query = query.filter(StatusRow.category == category)
    if date_from:
        query = query.filter(StatusRow.date >= date_from)
    if date_to:
        query = query.filter(StatusRow.date <= date_to)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (StatusRow.remarks.ilike(like))
            | (StatusRow.item_category.ilike(like))
            | (StatusRow.code_unit.ilike(like))
        )
    return query.order_by(StatusRow.date.desc()).limit(limit).all()


@router.get("/export")
def export_status(db: Session = Depends(get_db)):
    data = export_status_browse_xlsx(db)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=STATUS.xlsx"},
    )


@router.get("/count")
def status_count(db: Session = Depends(get_db)):
    return {"count": db.query(StatusRow).count()}