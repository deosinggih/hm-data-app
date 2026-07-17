from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MasterUnit, MasterVendor
from app.schemas import ImportResult, VendorUnitsOut
from app.services.excel_import import seed_master_from_form

router = APIRouter(prefix="/api/master", tags=["master"])


@router.get("/vendors-units", response_model=VendorUnitsOut)
def vendors_units(db: Session = Depends(get_db)):
    units = db.query(MasterUnit).order_by(MasterUnit.vendor, MasterUnit.code_unit).all()
    vendors = [v.name for v in db.query(MasterVendor).order_by(MasterVendor.name).all()]
    by: dict[str, list[str]] = {v: [] for v in vendors}
    for u in units:
        by.setdefault(u.vendor, []).append(u.code_unit)
        if u.vendor not in vendors:
            vendors.append(u.vendor)
    return VendorUnitsOut(vendors=vendors, units_by_vendor=by)


@router.post("/seed", response_model=ImportResult)
def seed_master(db: Session = Depends(get_db)):
    n = seed_master_from_form(db)
    return ImportResult(sheet="Master Unit", rows=n, message=f"Seeded/added {n} units from form HM.xlsx")


@router.post("/import", response_model=ImportResult)
async def import_master(file: UploadFile = File(...), db: Session = Depends(get_db)):
    from pathlib import Path
    from tempfile import NamedTemporaryFile

    content = await file.read()
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(content)
        path = Path(tmp.name)
    n = seed_master_from_form(db, path)
    path.unlink(missing_ok=True)
    return ImportResult(sheet="Master Unit", rows=n, message=f"Imported {n} new units")