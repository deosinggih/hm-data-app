from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.excel_export import export_form_hm_xlsx

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/data-hm")
def export_data_hm(db: Session = Depends(get_db)):
    data = export_form_hm_xlsx(db)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=form_DATA_HM.xlsx"},
    )