import base64
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.config import (
    BULAN_ID_PANJANG,
    COMPANY_ADDRESS_LINE1,
    COMPANY_ADDRESS_LINE2,
    COMPANY_NAME,
)
from app.services.ba_excel import BA_COLS
from app.database import get_db
from app.models import BaConfig, DataHmRow
from app.routers.pa import _hm_df, _po_df, _status_df
from app.schemas import BaConfigIn, BaConfigOut, BaPreviewOut
from app.services.ba_excel import (
    build_narasi,
    generate_ba_excel,
    generate_lampiran_excel,
)
from app.services.ba_pdf import generate_ba_pdf, generate_lampiran_all_pdf
from app.services.data_processor import (
    build_ba_rows,
    build_pa_rekap,
    process_core_data,
)
from app.services.lampiran_hm import apply_lampiran_hm_stop_adj

router = APIRouter(prefix="/api/ba", tags=["ba"])


def _get_or_create_config(db: Session) -> BaConfig:
    cfg = db.query(BaConfig).first()
    if not cfg:
        cfg = BaConfig()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _cfg_out(cfg: BaConfig) -> BaConfigOut:
    return BaConfigOut(
        id=cfg.id,
        no_ba=cfg.no_ba,
        lokasi_ttd=cfg.lokasi_ttd,
        vendor=cfg.vendor,
        nama_admin=cfg.nama_admin,
        nama_sp=cfg.nama_sp,
        nama_pm=cfg.nama_pm,
        nama_sig=cfg.nama_sig,
        nama_pjo=cfg.nama_pjo,
        nama_ml=cfg.nama_ml,
        nama_dibuat=cfg.nama_dibuat,
        jabatan_dibuat=cfg.jabatan_dibuat,
        nama_diperiksa=cfg.nama_diperiksa,
        jabatan_diperiksa=cfg.jabatan_diperiksa,
        nama_diketahui=cfg.nama_diketahui,
        jabatan_diketahui=cfg.jabatan_diketahui,
        has_ttd_admin=bool(cfg.ttd_admin),
        has_ttd_sp=bool(cfg.ttd_sp),
        has_ttd_pm=bool(cfg.ttd_pm),
        has_ttd_sig=bool(cfg.ttd_sig),
        has_ttd_pjo=bool(cfg.ttd_pjo),
        has_ttd_ml=bool(cfg.ttd_ml),
        has_ttd_dibuat=bool(cfg.ttd_dibuat),
        has_ttd_diperiksa=bool(cfg.ttd_diperiksa),
        has_ttd_diketahui=bool(cfg.ttd_diketahui),
    )


def _admin_vendor_label(vendor: str) -> str:
    """Jabatan PIC Diketahui di Lampiran: Admin + nama vendor Cover BA."""
    v = (vendor or "").strip()
    return f"Admin {v}" if v else "Admin Vendor"


_TTD_FIELDS = {
    "admin": "ttd_admin",
    "sp": "ttd_sp",
    "pm": "ttd_pm",
    "sig": "ttd_sig",
    "pjo": "ttd_pjo",
    "ml": "ttd_ml",
    "dibuat": "ttd_dibuat",
    "diperiksa": "ttd_diperiksa",
    "diketahui": "ttd_diketahui",
}


def _guess_image_media_type(raw: bytes) -> str:
    if raw.startswith(b"\x89PNG"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


@router.get("/config", response_model=BaConfigOut)
def get_config(db: Session = Depends(get_db)):
    return _cfg_out(_get_or_create_config(db))


@router.put("/config", response_model=BaConfigOut)
def put_config(payload: BaConfigIn, db: Session = Depends(get_db)):
    cfg = _get_or_create_config(db)
    for k, v in payload.model_dump().items():
        setattr(cfg, k, v)
    db.commit()
    db.refresh(cfg)
    return _cfg_out(cfg)


@router.post("/config/ttd/{role}")
async def upload_ttd(role: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    field = _TTD_FIELDS.get(role)
    if not field:
        raise HTTPException(status_code=400, detail="Unknown role")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File kosong")
    if len(content) > 3 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Maksimal 3 MB")
    cfg = _get_or_create_config(db)
    setattr(cfg, field, base64.b64encode(content).decode("ascii"))
    db.commit()
    return {"ok": True, "role": role, "has_ttd": True}


@router.get("/config/ttd/{role}")
def get_ttd(role: str, db: Session = Depends(get_db)):
    field = _TTD_FIELDS.get(role)
    if not field:
        raise HTTPException(status_code=400, detail="Unknown role")
    cfg = _get_or_create_config(db)
    b64 = getattr(cfg, field, None)
    if not b64:
        raise HTTPException(status_code=404, detail="TTD belum diunggah")
    raw = base64.b64decode(b64)
    return Response(
        content=raw,
        media_type=_guess_image_media_type(raw),
        headers={"Cache-Control": "no-store"},
    )


@router.delete("/config/ttd/{role}")
def delete_ttd(role: str, db: Session = Depends(get_db)):
    field = _TTD_FIELDS.get(role)
    if not field:
        raise HTTPException(status_code=400, detail="Unknown role")
    cfg = _get_or_create_config(db)
    setattr(cfg, field, None)
    db.commit()
    return {"ok": True, "role": role, "has_ttd": False}


def _compute_ba(db: Session, vendor: str | None = None):
    hm = _hm_df(db)
    st = _status_df(db)
    if hm.empty:
        return None, None, None
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
    df_hm, df_st, merged = process_core_data(hm, st)
    cfg = _get_or_create_config(db)
    vend = vendor or cfg.vendor
    if vend:
        merged = merged[merged["VENDOR"].astype(str).str.contains(vend.replace("PT.", "").strip(), case=False, na=False)
                        | (merged["VENDOR"] == vend)]
        if merged.empty:
            merged = process_core_data(hm, st)[2]
            if vend:
                merged = merged[merged["VENDOR"] == vend]
    recap = build_pa_rekap(merged, _po_df(db))
    ba = build_ba_rows(recap)
    return ba, merged, cfg


@router.get("/preview", response_model=BaPreviewOut)
def ba_preview(vendor: str | None = None, db: Session = Depends(get_db)):
    ba, merged, cfg = _compute_ba(db, vendor)
    if cfg is None:
        cfg = _get_or_create_config(db)
    if ba is None or ba.empty:
        return BaPreviewOut(
            vendor=vendor or cfg.vendor or "",
            title="BERITA ACARA PEMAKAIAN RENTAL UNIT",
            no_ba=cfg.no_ba,
            narasi="Belum ada data DATA HM",
            rows=[],
            tanggal_ttd="",
            company_name=COMPANY_NAME,
            company_address_line1=COMPANY_ADDRESS_LINE1,
            company_address_line2=COMPANY_ADDRESS_LINE2,
            columns=BA_COLS,
        )
    vend = vendor or cfg.vendor or (ba.iloc[0]["VENDOR"] if len(ba) else "")
    today = date.today()
    period = f"{BULAN_ID_PANJANG[today.month - 1]} {today.year}"
    if merged is not None and not merged.empty:
        dmin = merged["DATE_CLEAN"].min()
        period = f"{BULAN_ID_PANJANG[dmin.month - 1]} {dmin.year}"
    return BaPreviewOut(
        vendor=vend,
        title=f"BERITA ACARA PEMAKAIAN RENTAL UNIT {vend}",
        no_ba=cfg.no_ba,
        narasi=build_narasi(vend, period),
        rows=ba.to_dict(orient="records"),
        tanggal_ttd=f"{cfg.lokasi_ttd}, {today.day} {BULAN_ID_PANJANG[today.month - 1]} {today.year}",
        company_name=COMPANY_NAME,
        company_address_line1=COMPANY_ADDRESS_LINE1,
        company_address_line2=COMPANY_ADDRESS_LINE2,
        columns=BA_COLS,
    )


@router.get("/export")
def ba_export(vendor: str | None = None, db: Session = Depends(get_db)):
    ba, merged, cfg = _compute_ba(db, vendor)
    if cfg is None:
        cfg = _get_or_create_config(db)
    ttd_images = {
        "admin": cfg.ttd_admin,
        "sp": cfg.ttd_sp,
        "pm": cfg.ttd_pm,
        "sig": cfg.ttd_sig,
        "pjo": cfg.ttd_pjo,
        "ml": cfg.ttd_ml,
    }
    names = {
        "nama_admin": cfg.nama_admin,
        "nama_sp": cfg.nama_sp,
        "nama_pm": cfg.nama_pm,
        "nama_sig": cfg.nama_sig,
        "nama_pjo": cfg.nama_pjo,
        "nama_ml": cfg.nama_ml,
    }
    if ba is None or ba.empty:
        ba_empty = __import__("pandas").DataFrame()
        data = generate_ba_excel(
            ba_empty, vendor or cfg.vendor, cfg.no_ba, cfg.lokasi_ttd,
            names, "—", ttd_images=ttd_images,
        )
    else:
        vend = vendor or cfg.vendor or ba.iloc[0].get("VENDOR", "")
        today = date.today()
        period = f"{BULAN_ID_PANJANG[today.month - 1]} {today.year}"
        if merged is not None and not merged.empty:
            dmin = merged["DATE_CLEAN"].min()
            period = f"{BULAN_ID_PANJANG[dmin.month - 1]} {dmin.year}"
        data = generate_ba_excel(
            ba, vend, cfg.no_ba, cfg.lokasi_ttd, names, period, ttd_images=ttd_images,
        )
    fname = f"BA_{(vendor or cfg.vendor or 'UNIT').replace(' ', '_')}.xlsx"
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/export-pdf")
def ba_export_pdf(vendor: str | None = None, db: Session = Depends(get_db)):
    ba, merged, cfg = _compute_ba(db, vendor)
    if cfg is None:
        cfg = _get_or_create_config(db)
    ttd_images = {
        "admin": cfg.ttd_admin,
        "sp": cfg.ttd_sp,
        "pm": cfg.ttd_pm,
        "sig": cfg.ttd_sig,
        "pjo": cfg.ttd_pjo,
        "ml": cfg.ttd_ml,
    }
    names = {
        "nama_admin": cfg.nama_admin,
        "nama_sp": cfg.nama_sp,
        "nama_pm": cfg.nama_pm,
        "nama_sig": cfg.nama_sig,
        "nama_pjo": cfg.nama_pjo,
        "nama_ml": cfg.nama_ml,
    }
    today = date.today()
    vend = vendor or cfg.vendor or ""
    period = f"{BULAN_ID_PANJANG[today.month - 1]} {today.year}"
    if ba is not None and not ba.empty:
        vend = vendor or cfg.vendor or ba.iloc[0].get("VENDOR", "") or vend
    if merged is not None and not merged.empty:
        dmin = merged["DATE_CLEAN"].min()
        period = f"{BULAN_ID_PANJANG[dmin.month - 1]} {dmin.year}"
    tanggal_ttd = (
        f"{cfg.lokasi_ttd}, {today.day} {BULAN_ID_PANJANG[today.month - 1]} {today.year}"
    )
    import pandas as pd
    ba_df = ba if ba is not None else pd.DataFrame()
    data = generate_ba_pdf(
        ba_df, vend, cfg.no_ba, cfg.lokasi_ttd, names, period, tanggal_ttd,
        ttd_images=ttd_images,
    )
    fname = f"BA_{(vend or 'UNIT').replace(' ', '_')}.pdf"
    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.get("/lampiran")
def lampiran_preview(
    unit: str | None = None,
    vendor: str | None = None,
    db: Session = Depends(get_db),
):
    cfg = _get_or_create_config(db)
    vend = vendor or cfg.vendor or None
    ba, merged, cfg = _compute_ba(db, vend)
    if cfg is None:
        cfg = _get_or_create_config(db)
    if merged is None or merged.empty:
        return {"units": [], "unit_options": [], "rows": [], "pa": 0}

    # Kode unit sama dengan daftar Summary PA (recap PA)
    recap = build_pa_rekap(merged, _po_df(db))
    if vend and len(recap):
        recap = recap[
            (recap["VENDOR"] == vend)
            | recap["VENDOR"].astype(str).str.contains(
                vend.replace("PT.", "").replace("PT ", "").strip(),
                case=False,
                na=False,
            )
        ]
    unit_options = [
        {
            "code_unit": str(r.get("CODE UNIT") or ""),
            "vendor": str(r.get("VENDOR") or ""),
            "pa": round(float(r.get("PA (%)") or 0), 2),
            "equipment": str(r.get("EQUIPMENT") or r.get("Type Alat") or ""),
        }
        for r in recap.to_dict(orient="records")
        if r.get("CODE UNIT")
    ]
    units = [o["code_unit"] for o in unit_options]
    if not units:
        units = sorted(str(u) for u in merged["CODE UNIT"].dropna().unique().tolist())
        unit_options = [{"code_unit": u, "vendor": "", "pa": 0, "equipment": ""} for u in units]

    code = unit if unit in units else (units[0] if units else None)
    if not code:
        return {"units": [], "unit_options": [], "rows": [], "pa": 0}
    sub = merged[merged["CODE UNIT"] == code].sort_values(["DATE_CLEAN", "SHIFT_NUM"])
    jam = float(sub.assign(TOTAL=12)["TOTAL"].sum())
    bd = float(sub["BD"].sum())
    pa = round(((jam - bd) / jam) * 100, 2) if jam else 0

    hm_rows = db.query(DataHmRow).filter(DataHmRow.code_unit == code).all()
    hm_map: dict[tuple[str, str], DataHmRow] = {}
    for h in hm_rows:
        shift_key = str(h.shift or "")
        hm_map[(str(h.date), shift_key)] = h
        # also index by "Shift N" / bare number
        digits = "".join(ch for ch in shift_key if ch.isdigit())
        if digits:
            hm_map[(str(h.date), f"Shift {digits}")] = h
            hm_map[(str(h.date), digits)] = h

    # Type / tahun from BA recap (PO)
    type_unit = ""
    th_unit = ""
    if ba is not None and not ba.empty:
        match = ba[ba["CODE UNIT"] == code]
        if len(match):
            type_unit = str(match.iloc[0].get("Type Alat") or "")
            th_unit = str(match.iloc[0].get("Tahun Unit") or "")

    rows = []
    for r in sub.itertuples():
        shift_label = f"Shift {r.SHIFT_NUM}"
        hm = hm_map.get((str(r.DATE_CLEAN), shift_label)) or hm_map.get((str(r.DATE_CLEAN), str(r.SHIFT_NUM)))
        hm_start = round(float(hm.hm_start), 2) if hm and hm.hm_start is not None else 0.0
        hm_stop = round(float(hm.hm_stop), 2) if hm and hm.hm_stop is not None else 0.0
        working = round(float(r.WORKING_VAL or 0), 2)
        rows.append({
            "DATE": str(r.DATE_CLEAN),
            "SHIFT": shift_label,
            "HM_START": hm_start,
            "HM_STOP": hm_stop,
            "HM_STOP_ADJ": hm_stop,  # diisi ulang di bawah (rumus Excel col G)
            "HM_NOT_WORKING": 0.0,
            "HM_WORKING": working,
            "WORKING": working,
            "BD": round(float(r.BD or 0), 2),
            "FM": round(float(r.JAM_FM or 0), 2),
            "STBY": round(float(r.STBY or 0), 2),
            "POT_Z": round(float(r.POT_Z or 0), 2),
            "AREA": (hm.located if hm else "") or "",
            "PEKERJAAN": (hm.job_description if hm else "") or "",
            # Excel Lampiran col O = FILTER INFORMATION (DATA HM!X), bukan kolom Keterangan bebas
            "KETERANGAN": (hm.information if hm else "") or "",
            "INFORMATION": (hm.information if hm else "") or "",
        })

    apply_lampiran_hm_stop_adj(rows)

    subtotal = {
        "HM_WORKING": round(sum(x["HM_WORKING"] for x in rows), 2),
        "BD": round(sum(x["BD"] for x in rows), 2),
        "FM": round(sum(x["FM"] for x in rows), 2),
        "STBY": round(sum(x["STBY"] for x in rows), 2),
    }
    vendor_cover = (cfg.vendor or (sub.iloc[0]["VENDOR"] if len(sub) else "") or "").strip()
    return {
        "units": units,
        "unit_options": unit_options,
        "unit": code,
        "pa": pa,
        "type_unit": type_unit,
        "th_unit": th_unit,
        "rows": rows,
        "subtotal": subtotal,
        "vendor": vendor_cover,
        "names": {
            "nama_dibuat": cfg.nama_dibuat,
            "jabatan_dibuat": cfg.jabatan_dibuat,
            "nama_diperiksa": cfg.nama_diperiksa,
            "jabatan_diperiksa": cfg.jabatan_diperiksa,
            "nama_diketahui": cfg.nama_diketahui,
            # Selalu ikut vendor Cover BA (bukan teks lama spt Admin CV. AHG)
            "jabatan_diketahui": _admin_vendor_label(vendor_cover),
        },
    }


@router.get("/lampiran/export")
def lampiran_export(unit: str, db: Session = Depends(get_db)):
    preview = lampiran_preview(unit=unit, db=db)
    cfg = _get_or_create_config(db)
    data = generate_lampiran_excel(
        preview["rows"],
        preview.get("unit") or unit,
        preview.get("pa") or 0,
        preview.get("names") or {},
        preview.get("vendor") or cfg.vendor,
        type_unit=preview.get("type_unit") or "",
        th_unit=preview.get("th_unit") or "",
        ttd_images={
            "dibuat": cfg.ttd_dibuat,
            "diperiksa": cfg.ttd_diperiksa,
            "diketahui": cfg.ttd_diketahui,
        },
    )
    safe = (unit or "unit")[:28].replace("/", "-")
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Lampiran_{safe}.xlsx"},
    )


@router.get("/lampiran/export-pdf")
def lampiran_export_pdf(vendor: str | None = None, db: Session = Depends(get_db)):
    """Export PDF semua unit yang ada di dropdown Lampiran (Summary PA)."""
    first = lampiran_preview(unit=None, vendor=vendor, db=db)
    units = first.get("units") or []
    cfg = _get_or_create_config(db)
    ttd_images = {
        "dibuat": cfg.ttd_dibuat,
        "diperiksa": cfg.ttd_diperiksa,
        "diketahui": cfg.ttd_diketahui,
    }
    units_data = []
    for u in units:
        units_data.append(lampiran_preview(unit=u, vendor=vendor, db=db))
    data = generate_lampiran_all_pdf(units_data, ttd_images=ttd_images)
    vend = (first.get("vendor") or cfg.vendor or "ALL").replace(" ", "_")
    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Lampiran_Semua_Unit_{vend}.pdf"},
    )