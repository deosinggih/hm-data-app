from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PoUnitRow
from app.schemas import ImportResult
from app.services.excel_import import import_po_excel

router = APIRouter(prefix="/api/po", tags=["po"])


@router.post("/import", response_model=ImportResult)
async def import_po(
    file: UploadFile = File(...),
    replace: bool = True,
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        n = import_po_excel(db, content, replace=replace)
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    return ImportResult(sheet="PO Unit", rows=n, message=f"Imported {n} PO rows")


@router.get("")
def list_po(db: Session = Depends(get_db)):
    rows = db.query(PoUnitRow).limit(2000).all()
    return [
        {
            "id": r.id,
            "vendor": r.vendor,
            "po_number": r.po_number,
            "equipment": r.equipment,
            "year": r.year,
            "code_unit_mcr": r.code_unit_mcr,
            "periode_str": r.periode_str,
        }
        for r in rows
    ]