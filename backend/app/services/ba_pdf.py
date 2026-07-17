"""PDF export for COVER BA and Lampiran (all units).

Warna & layout mengikuti Excel COVER BA / Lampiran.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepInFrame,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import COMPANY_ADDRESS_LINE1, COMPANY_ADDRESS_LINE2, COMPANY_NAME
from app.services.ba_excel import BA_COLS, build_narasi

HEADER_BG = colors.HexColor("#BFBFBF")
TAGIH_BG = colors.HexColor("#F2F2F2")
SOFT_BG = colors.HexColor("#D9E1F2")
SUB_BG = colors.HexColor("#FFFF00")

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 8 * mm
USABLE_W = PAGE_W - 2 * MARGIN
USABLE_H = PAGE_H - 2 * MARGIN
TTD_RESERVE_BA = 58 * mm
TTD_RESERVE_LAMP = 42 * mm


def _styles():
    base = getSampleStyleSheet()
    return {
        "kop": ParagraphStyle(
            "kop", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=14, alignment=TA_CENTER, spaceBefore=0, spaceAfter=1,
        ),
        "alamat": ParagraphStyle(
            "alamat", parent=base["Normal"], fontName="Times-Roman",
            fontSize=7, alignment=TA_CENTER, leading=9, spaceAfter=0,
        ),
        "judul": ParagraphStyle(
            "judul", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, alignment=TA_CENTER, spaceBefore=8, spaceAfter=2,
        ),
        "no": ParagraphStyle(
            "no", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, alignment=TA_CENTER, spaceAfter=6,
        ),
        "narasi": ParagraphStyle(
            "narasi", parent=base["Normal"], fontName="Helvetica",
            fontSize=8, alignment=TA_LEFT, leading=11, spaceAfter=6,
        ),
        "center": ParagraphStyle(
            "center", parent=base["Normal"], fontName="Helvetica",
            fontSize=8, alignment=TA_CENTER,
        ),
        "center_b": ParagraphStyle(
            "center_b", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, alignment=TA_CENTER,
        ),
        "tgl_ttd": ParagraphStyle(
            "tgl_ttd", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, alignment=TA_LEFT, spaceAfter=6,
        ),
        "title_l": ParagraphStyle(
            "title_l", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, alignment=TA_CENTER, spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "meta", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, alignment=TA_LEFT, leading=12,
        ),
        "meta_r": ParagraphStyle(
            "meta_r", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, alignment=TA_RIGHT, leading=12,
        ),
    }


def _img_from_b64(b64: str | None, max_w=50, max_h=24):
    if not b64:
        return Spacer(max_w, max_h)
    try:
        raw = base64.b64decode(b64)
        bio = BytesIO(raw)
        img = Image(bio, width=max_w, height=max_h, kind="proportional")
        img.hAlign = "CENTER"
        return img
    except Exception:
        return Spacer(max_w, max_h)


def _ttd_block(styles, inst: str, role: str, nama: str, jabatan: str, b64: str | None, width: float):
    return Table(
        [
            [Paragraph(inst or " ", styles["center_b"])],
            [Paragraph(role or " ", styles["center"])],
            [_img_from_b64(b64)],
            [Paragraph(f"<u>{nama or '&nbsp;'}</u>", styles["center_b"])],
            [Paragraph(jabatan or " ", styles["center"])],
        ],
        colWidths=[width],
    )


def _fmt_num(v: Any) -> str:
    """Angka max 2 desimal, English: decimal `.`, thousand `,` (1,234.56)."""
    try:
        n = round(float(v), 2)
    except (TypeError, ValueError):
        return "" if v is None else str(v)
    sign = "-" if n < 0 else ""
    abs_n = abs(n)
    if abs_n == int(abs_n):
        body = f"{int(abs_n):,}"
    else:
        body = f"{abs_n:,.2f}".rstrip("0").rstrip(".")
    return f"{sign}{body}"


def _auto_widths(headers: list[str], body: list[list], total_w: float, min_w: float = 16, max_frac: float = 0.18) -> list[float]:
    """Lebar kolom proporsional ke konten; header panjang dihitung per baris (wrap 2)."""
    n = len(headers)
    if n == 0:
        return []
    weights: list[float] = []
    for i, h in enumerate(headers):
        parts = str(h).replace("<br/>", "\n").split("\n")
        hlen = max((len(p.strip()) for p in parts), default=1)
        dlen = 1
        for row in body:
            if i < len(row):
                dlen = max(dlen, len(str(row[i] or "")))
        # Data teks panjang dibatasi agar tidak menelan kolom lain
        weights.append(float(max(hlen, min(dlen, 10))))
    s = sum(weights) or n
    max_w = total_w * max_frac
    widths = [max(min_w, total_w * (w / s)) for w in weights]
    widths = [min(w, max_w) for w in widths]
    # renormalize ke total_w
    scale = total_w / (sum(widths) or 1)
    return [w * scale for w in widths]


def _fmt_ba_cell(col: str, v: Any) -> str:
    if col == "PA Unit":
        try:
            return f"{_fmt_num(float(v) * 100)}%"
        except (TypeError, ValueError):
            return ""
    if col == "Tahun Unit":
        if v is None or v == "":
            return ""
        s = str(v).strip()
        return s[:-2] if s.endswith(".0") else s
    if col in (
        "Total HM Sebelum Dipotong", "Total Pemotongan HM", "BD & No Operator",
        "Standby Force Majeure", "Standby Schedule", "TOTAL HM",
        "PA<80%", "PA>90%", "HM Yang Ditagihkan",
    ):
        return _fmt_num(v)
    return "" if v is None else str(v)


def _pin_page(top_flowables: list, bottom_flowables: list, ttd_reserve: float) -> Flowable:
    """Satu halaman: judul di atas, TTD di bawah, isi di antaranya."""
    top_h = max(USABLE_H - ttd_reserve, 40 * mm)
    top = KeepInFrame(USABLE_W, top_h, top_flowables, mode="shrink", hAlign="LEFT", vAlign="TOP")
    bottom = KeepInFrame(USABLE_W, ttd_reserve, bottom_flowables, mode="shrink", hAlign="LEFT", vAlign="BOTTOM")
    outer = Table(
        [[top], [bottom]],
        colWidths=[USABLE_W],
        rowHeights=[top_h, ttd_reserve],
    )
    outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("VALIGN", (0, 1), (0, 1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return outer


def generate_ba_pdf(
    ba_df: pd.DataFrame,
    vendor: str,
    no_ba: str,
    lokasi_ttd: str,
    names: dict[str, str],
    period_label: str,
    tanggal_ttd: str,
    ttd_images: dict[str, str | None] | None = None,
) -> bytes:
    styles = _styles()
    ttd_images = ttd_images or {}
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    # --- TOP: sama Excel COVER BA (kop → alamat → judul → tabel) ---
    top: list = [
        Paragraph(COMPANY_NAME, styles["kop"]),
        Paragraph(COMPANY_ADDRESS_LINE1, styles["alamat"]),
        Paragraph(COMPANY_ADDRESS_LINE2, styles["alamat"]),
        Paragraph(f"<u>BERITA ACARA PEMAKAIAN RENTAL UNIT {vendor}</u>", styles["judul"]),
        Paragraph(f"No.{no_ba}", styles["no"]),
        Paragraph(build_narasi(vendor, period_label), styles["narasi"]),
    ]

    short = {
        "Total HM Sebelum Dipotong": "HM Sblm\nPotong",
        "Total Pemotongan HM": "Potong\nHM",
        "BD & No Operator": "BD &\nNo Op",
        "Standby Force Majeure": "STBY\nFM",
        "Standby Schedule": "STBY\nSched",
        "HM Yang Ditagihkan": "HM\nDitagihkan",
        "KETERANGAN PEKERJAAN": "Keterangan",
        "Periode PO": "Periode\nPO",
        "Type Alat": "Type\nAlat",
        "Tahun Unit": "Th\nUnit",
        "PA Unit": "PA\nUnit",
    }
    header = [short.get(c, c) for c in BA_COLS]
    data = [header]
    rows = ba_df.to_dict(orient="records") if ba_df is not None and not ba_df.empty else []
    for r in rows:
        data.append([_fmt_ba_cell(c, r.get(c, "")) for c in BA_COLS])
    if rows:
        totals = []
        for c in BA_COLS:
            if c == "PO Numb.":
                totals.append("Grand Total")
            elif c in (
                "Total HM Sebelum Dipotong", "Total Pemotongan HM", "BD & No Operator",
                "Standby Force Majeure", "Standby Schedule", "TOTAL HM",
                "PA<80%", "PA>90%", "HM Yang Ditagihkan",
            ):
                try:
                    totals.append(_fmt_num(pd.to_numeric(ba_df[c], errors="coerce").fillna(0).sum()))
                except Exception:
                    totals.append("")
            else:
                totals.append("")
        data.append(totals)

    widths = _auto_widths(header, data[1:], USABLE_W, min_w=14, max_frac=0.14)
    tbl = Table(data, colWidths=widths, repeatRows=1)
    style_cmds = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    tagih_i = BA_COLS.index("HM Yang Ditagihkan")
    if len(data) > 1:
        style_cmds.append(("BACKGROUND", (tagih_i, 1), (tagih_i, -2 if rows else -1), TAGIH_BG))
    if rows:
        style_cmds.append(("BACKGROUND", (0, -1), (-1, -1), HEADER_BG))
        style_cmds.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    tbl.setStyle(TableStyle(style_cmds))
    top.append(tbl)

    # --- BOTTOM: tanggal + TTD ---
    bottom: list = [
        Paragraph(tanggal_ttd, styles["tgl_ttd"]),
        Spacer(1, 6),
    ]
    tier1 = [
        (COMPANY_NAME, "Dibuat Oleh,", names.get("nama_admin", ""), "Admin Project", "admin"),
        (COMPANY_NAME, "Mengetahui,", names.get("nama_sp", ""), "Superintendent Project", "sp"),
        (COMPANY_NAME, "Diperiksa Oleh,", names.get("nama_pm", ""), "Manager Project PT. KAN", "pm"),
        (COMPANY_NAME, "Mengetahui,", names.get("nama_sig", ""), "SIG", "sig"),
    ]
    w1 = USABLE_W / 4
    t1 = Table([[
        _ttd_block(styles, inst, role, nm, jb, ttd_images.get(key), w1)
        for inst, role, nm, jb, key in tier1
    ]], colWidths=[w1] * 4)
    t1.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    bottom.append(t1)
    bottom.append(Spacer(1, 8))

    vs = vendor.upper().replace("PT.", "").replace("PT ", "").strip()
    tier2 = [
        (f"PT. {vs}", "Disetujui Oleh,", names.get("nama_pjo", ""), "Penanggung Jawab Operasional", "pjo"),
        (COMPANY_NAME, "Diketahui Oleh,", names.get("nama_ml", ""), "Manager Logistik dan Commercial", "ml"),
    ]
    w2 = USABLE_W / 2
    t2 = Table([[
        _ttd_block(styles, inst, role, nm, jb, ttd_images.get(key), w2)
        for inst, role, nm, jb, key in tier2
    ]], colWidths=[w2] * 2)
    t2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    bottom.append(t2)

    doc.build([_pin_page(top, bottom, TTD_RESERVE_BA)])
    return buf.getvalue()


def _lampiran_page_flowable(styles: dict, unit_data: dict[str, Any], ttd_images: dict[str, str | None]) -> Flowable:
    vendor = unit_data.get("vendor") or ""
    unit = unit_data.get("unit") or ""
    names = unit_data.get("names") or {}
    rows = unit_data.get("rows") or []
    sub = unit_data.get("subtotal") or {}
    pa = unit_data.get("pa") or 0
    type_unit = unit_data.get("type_unit") or "—"
    th_unit = unit_data.get("th_unit") or "—"

    # TOP: judul
    top: list = [
        Paragraph(
            f"DAILY REKAPITULASI PEMAKAIAN UNIT RENTAL {vendor}",
            styles["title_l"],
        ),
    ]
    meta = Table(
        [[
            Paragraph(
                f"<b>Type Unit&nbsp;&nbsp;&nbsp;:</b> {type_unit}<br/>"
                f"<b>Code Unit :</b> {unit}",
                styles["meta"],
            ),
            Paragraph(
                f"<b>Th Unit:</b> {th_unit}<br/>"
                f"<b>PA :</b> {_fmt_num(pa)}%",
                styles["meta_r"],
            ),
        ]],
        colWidths=[USABLE_W * 0.5, USABLE_W * 0.5],
    )
    meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    top.append(meta)
    top.append(Spacer(1, 4))

    head1 = [
        "DATE", "SHIFT", "HM\nStart", "HM\nStop", "HM\nStop", "HM Not\nWorking",
        "HM\nWorking", "BD &\nNo Op", "STBY\nFM", "STBY\nSched", "AREA\nKERJA", "PEKERJAAN", "KETERANGAN",
    ]
    data = [head1]
    for r in rows:
        data.append([
            str(r.get("DATE", "")),
            str(r.get("SHIFT", "")),
            _fmt_num(r.get("HM_START")),
            _fmt_num(r.get("HM_STOP")),
            _fmt_num(r.get("HM_STOP_ADJ", r.get("HM_STOP"))),
            _fmt_num(r.get("HM_NOT_WORKING")),
            _fmt_num(r.get("HM_WORKING", r.get("WORKING"))),
            _fmt_num(r.get("BD")),
            _fmt_num(r.get("FM")),
            _fmt_num(r.get("STBY")),
            str(r.get("AREA") or ""),
            str(r.get("PEKERJAAN") or ""),
            str(r.get("KETERANGAN") or r.get("INFORMATION") or ""),
        ])
    data.append([
        "SUBTOTAL", "", "", "", "", "",
        _fmt_num(sub.get("HM_WORKING")),
        _fmt_num(sub.get("BD")),
        _fmt_num(sub.get("FM")),
        _fmt_num(sub.get("STBY")),
        "", "", "",
    ])
    widths = _auto_widths(head1, data[1:], USABLE_W, min_w=16, max_frac=0.14)
    tbl = Table(data, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, 0), SOFT_BG),
        ("BACKGROUND", (0, -1), (-1, -1), SUB_BG),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    top.append(tbl)

    # BOTTOM: TTD
    blocks = [
        ("Dibuat Oleh,", names.get("nama_dibuat", ""), names.get("jabatan_dibuat", ""), "dibuat"),
        ("Diperiksa Oleh,", names.get("nama_diperiksa", ""), names.get("jabatan_diperiksa", ""), "diperiksa"),
        ("Diketahui Oleh,", names.get("nama_diketahui", ""), names.get("jabatan_diketahui", ""), "diketahui"),
    ]
    w3 = USABLE_W / 3
    ttd = Table([[
        _ttd_block(styles, "", role, nm, jb, ttd_images.get(key), w3)
        for role, nm, jb, key in blocks
    ]], colWidths=[w3] * 3)
    ttd.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    bottom = [ttd]

    return _pin_page(top, bottom, TTD_RESERVE_LAMP)


def generate_lampiran_all_pdf(
    units_data: list[dict[str, Any]],
    ttd_images: dict[str, str | None] | None = None,
) -> bytes:
    """Satu halaman per unit; tiap halaman: judul di atas, TTD di bawah."""
    styles = _styles()
    ttd_images = ttd_images or {}
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    story: list = []
    if not units_data:
        story.append(Paragraph("Tidak ada unit untuk diekspor.", styles["center"]))
    else:
        for i, unit_data in enumerate(units_data):
            if i:
                story.append(PageBreak())
            story.append(_lampiran_page_flowable(styles, unit_data, ttd_images))
    doc.build(story)
    return buf.getvalue()
