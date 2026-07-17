from __future__ import annotations

import base64
from datetime import date
from io import BytesIO

import pandas as pd
from xlsxwriter import Workbook

from app.config import (
    BULAN_ID_PANJANG,
    COMPANY_ADDRESS_LINE1,
    COMPANY_ADDRESS_LINE2,
    COMPANY_NAME,
    HARI_ID,
)
from app.services.utils_terbilang import terbilang


# Flat column keys used in BA data rows (Status group split in Excel UI)
BA_COLS = [
    "No", "PO Numb.", "Periode PO", "Type Alat", "No Unit", "Tahun Unit",
    "PA Unit", "Total HM Sebelum Dipotong", "Total Pemotongan HM",
    "BD & No Operator", "Standby Force Majeure", "Standby Schedule",
    "TOTAL HM", "PA<80%", "PA>90%", "HM Yang Ditagihkan", "KETERANGAN PEKERJAAN",
]

# Excel-like palette (COVER BA / Lampiran workbook)
COLOR_HEADER = "#BFBFBF"
COLOR_TAGIH = "#F2F2F2"
COLOR_PICK = "#00B0F0"
COLOR_SUBTOTAL = "#FFFF00"
COLOR_HEAD_SOFT = "#D9E1F2"


def _auto_col_width(label: str, samples: list | None = None, min_w: float = 5, max_w: float = 16) -> float:
    """Lebar kolom Excel: header panjang di-wrap ~2 baris → width ≈ setengah panjang label."""
    samples = samples or []
    label = str(label or "")
    # Prefer wrap 2 baris: lebar mengikuti baris terpanjang setelah potong tengah
    if len(label) <= 10:
        h_w = len(label) + 1.5
    else:
        mid = (len(label) + 1) // 2
        sp = label.rfind(" ", 0, mid + 2)
        if sp < 3:
            sp = mid
        line1, line2 = label[:sp].strip(), label[sp:].strip()
        h_w = max(len(line1), len(line2), 1) + 1.5
    d_w = 0.0
    for s in samples[:40]:
        if s is None:
            continue
        d_w = max(d_w, len(str(s)))
    # Data angka biasanya pendek; jangan biarkan melebar berlebihan
    d_w = min(d_w + 1.2, max_w)
    return max(min_w, min(max_w, max(h_w, d_w)))


def build_narasi(vendor: str, period_label: str, today: date | None = None) -> str:
    today = today or date.today()
    return (
        f"Pada Hari {HARI_ID[today.weekday()]} "
        f"Tanggal {terbilang(today.day)} "
        f"Bulan {BULAN_ID_PANJANG[today.month - 1]} "
        f"Tahun {terbilang(today.year)}, "
        f"telah dilakukan rekapitulasi Hour Meter (HM) "
        f"Menggunakan Alat Rental milik {vendor} "
        f"Periode {period_label} sesuai dengan data sebagai berikut:"
    )


def generate_ba_excel(
    ba_df: pd.DataFrame,
    vendor: str,
    no_ba: str,
    lokasi_ttd: str,
    names: dict[str, str],
    period_label: str,
    ttd_images: dict[str, str | None] | None = None,
) -> bytes:
    today = date.today()
    narasi = build_narasi(vendor, period_label, today)
    tanggal_ttd = f"{lokasi_ttd}, {today.day} {BULAN_ID_PANJANG[today.month - 1]} {today.year}"

    out = BytesIO()
    wb = Workbook(out, {"in_memory": True})
    ws = wb.add_worksheet("COVER BA")

    f_kop = wb.add_format({"bold": True, "align": "center", "font_name": "Calibri", "font_size": 18})
    f_alamat = wb.add_format({"align": "center", "font_name": "Times New Roman", "font_size": 9})
    f_judul = wb.add_format({
        "bold": True, "align": "center", "font_size": 12,
        "underline": True, "font_name": "Calibri",
    })
    f_no = wb.add_format({"align": "center", "font_name": "Calibri", "font_size": 10})
    f_narasi = wb.add_format({
        "align": "left", "valign": "top", "font_name": "Calibri",
        "font_size": 9, "text_wrap": True,
    })
    f_head = wb.add_format({
        "bold": True, "align": "center", "valign": "vcenter",
        "font_name": "Calibri", "font_size": 8, "border": 1, "bg_color": COLOR_HEADER,
    })
    f_cell = wb.add_format({"font_name": "Calibri", "font_size": 8, "border": 1, "align": "center"})
    f_pct = wb.add_format({
        "font_name": "Calibri", "font_size": 8, "border": 1,
        "num_format": "#,##0%", "align": "center",
    })
    f_num = wb.add_format({
        "font_name": "Calibri", "font_size": 8, "border": 1,
        "num_format": "#,##0", "align": "center",
    })
    f_tagih = wb.add_format({
        "font_name": "Calibri", "font_size": 8, "border": 1,
        "num_format": "#,##0", "align": "center", "bg_color": COLOR_TAGIH,
    })
    f_center = wb.add_format({"align": "center", "font_name": "Calibri", "font_size": 9})
    f_inst = wb.add_format({"bold": True, "align": "center", "font_name": "Calibri", "font_size": 9})
    f_tgl_ttd = wb.add_format({"bold": True, "align": "left", "font_name": "Calibri", "font_size": 8})
    f_nama = wb.add_format({
        "bold": True, "align": "center", "underline": True,
        "font_name": "Calibri", "font_size": 9,
    })
    f_total_lab = wb.add_format({
        "bold": True, "align": "center", "font_name": "Calibri",
        "font_size": 9, "border": 1, "bg_color": COLOR_HEADER,
    })
    f_total_num = wb.add_format({
        "bold": True, "align": "center", "font_name": "Calibri",
        "font_size": 8, "border": 1, "num_format": "#,##0", "bg_color": COLOR_HEADER,
    })

    start_col = 5  # column F
    n_cols = len(BA_COLS)
    fc, lc = start_col, start_col + n_cols - 1

    ws.merge_range(4, fc, 4, lc, COMPANY_NAME, f_kop)
    ws.merge_range(5, fc, 5, lc, COMPANY_ADDRESS_LINE1, f_alamat)
    ws.merge_range(6, fc, 6, lc, COMPANY_ADDRESS_LINE2, f_alamat)
    ws.merge_range(8, fc, 8, lc, f"BERITA ACARA PEMAKAIAN RENTAL UNIT {vendor}", f_judul)
    ws.merge_range(9, fc, 9, lc, f"No.{no_ba}", f_no)
    ws.merge_range(11, fc, 12, lc, narasi, f_narasi)

    # Two-row header like workbook: Status spans BD / FM / STBY
    header_row = 14
    # Row 1: merge Status over BD / FM / STBY; other headers span 2 rows
    c = start_col
    i = 0
    while i < n_cols:
        col = BA_COLS[i]
        if col == "BD & No Operator":
            ws.merge_range(header_row, c, header_row, c + 2, "Status", f_head)
            c += 3
            i += 3
        else:
            ws.merge_range(header_row, c, header_row + 1, c, col, f_head)
            c += 1
            i += 1
    for label in ("BD & No Operator", "Standby Force Majeure", "Standby Schedule"):
        ws.write(header_row + 1, start_col + BA_COLS.index(label), label, f_head)

    data_start = header_row + 2
    for r_i, row in enumerate(ba_df.to_dict(orient="records")):
        excel_r = data_start + r_i
        for c_i, col in enumerate(BA_COLS):
            val = row.get(col, "")
            cell = start_col + c_i
            if col == "PA Unit":
                ws.write(excel_r, cell, float(val or 0), f_pct)
            elif col == "Tahun Unit":
                # Tahun tanpa separator ribuan (hindari 2.024)
                ys = "" if val is None or (isinstance(val, float) and pd.isna(val)) else str(val).strip()
                if ys.endswith(".0"):
                    ys = ys[:-2]
                ws.write(excel_r, cell, ys, f_cell)
            elif col == "HM Yang Ditagihkan":
                try:
                    ws.write(excel_r, cell, float(val or 0), f_tagih)
                except (TypeError, ValueError):
                    ws.write(excel_r, cell, val, f_cell)
            elif col in (
                "Total HM Sebelum Dipotong", "Total Pemotongan HM", "BD & No Operator",
                "Standby Force Majeure", "Standby Schedule", "TOTAL HM",
                "PA<80%", "PA>90%",
            ):
                try:
                    ws.write(excel_r, cell, float(val or 0), f_num)
                except (TypeError, ValueError):
                    ws.write(excel_r, cell, val, f_cell)
            else:
                ws.write(excel_r, cell, val if val is not None else "", f_cell)

    # Grand Total
    total_r = data_start + len(ba_df)
    if len(ba_df):
        ws.merge_range(total_r, start_col + 1, total_r, start_col + 3, "Grand Total", f_total_lab)
        for col in (
            "Total HM Sebelum Dipotong", "Total Pemotongan HM", "BD & No Operator",
            "Standby Force Majeure", "Standby Schedule", "TOTAL HM",
            "PA<80%", "PA>90%", "HM Yang Ditagihkan",
        ):
            c_i = BA_COLS.index(col)
            try:
                total = float(pd.to_numeric(ba_df[col], errors="coerce").fillna(0).sum())
            except Exception:
                total = 0.0
            ws.write(total_r, start_col + c_i, int(round(total)), f_total_num)

    last_r = total_r + 4
    ws.merge_range(last_r, start_col + 1, last_r, start_col + 4, tanggal_ttd, f_tgl_ttd)
    ttd_images = ttd_images or {}

    tier1 = [
        ("Dibuat Oleh,", names.get("nama_admin", ""), "Admin Project", "admin"),
        ("Mengetahui,", names.get("nama_sp", ""), "Superintendent Project", "sp"),
        ("Diperiksa Oleh,", names.get("nama_pm", ""), "Manager Project PT. KAN", "pm"),
        ("Mengetahui,", names.get("nama_sig", ""), "SIG", "sig"),
    ]
    for ci, (role, nm, jb, key) in enumerate(tier1):
        c0 = start_col + 1 + ci * 4
        c1 = c0 + 3
        ws.merge_range(last_r + 2, c0, last_r + 2, c1, COMPANY_NAME, f_inst)
        ws.merge_range(last_r + 3, c0, last_r + 3, c1, role, f_center)
        _insert_ttd_image(ws, last_r + 4, c0, ttd_images.get(key), scale=0.32)
        ws.merge_range(last_r + 8, c0, last_r + 8, c1, nm, f_nama)
        ws.merge_range(last_r + 9, c0, last_r + 9, c1, jb, f_center)

    vs = vendor.upper().replace("PT.", "").replace("PT ", "").strip()
    c0_pjo, c1_pjo = start_col + 1, start_col + 8
    c0_ml, c1_ml = start_col + 9, start_col + 16
    ws.merge_range(last_r + 14, c0_pjo, last_r + 14, c1_pjo, f"PT. {vs}", f_inst)
    ws.merge_range(last_r + 14, c0_ml, last_r + 14, c1_ml, COMPANY_NAME, f_inst)
    ws.merge_range(last_r + 15, c0_pjo, last_r + 15, c1_pjo, "Disetujui Oleh,", f_center)
    ws.merge_range(last_r + 15, c0_ml, last_r + 15, c1_ml, "Diketahui Oleh,", f_center)
    _insert_ttd_image(ws, last_r + 16, c0_pjo, ttd_images.get("pjo"), scale=0.32)
    _insert_ttd_image(ws, last_r + 16, c0_ml, ttd_images.get("ml"), scale=0.32)
    ws.merge_range(last_r + 20, c0_pjo, last_r + 20, c1_pjo, names.get("nama_pjo", ""), f_nama)
    ws.merge_range(last_r + 20, c0_ml, last_r + 20, c1_ml, names.get("nama_ml", ""), f_nama)
    ws.merge_range(last_r + 21, c0_pjo, last_r + 21, c1_pjo, "Penanggung Jawab Operasional", f_center)
    ws.merge_range(last_r + 21, c0_ml, last_r + 21, c1_ml, "Manager Logistik dan Commercial", f_center)

    records = ba_df.to_dict(orient="records") if ba_df is not None and not ba_df.empty else []
    for i, col_name in enumerate(BA_COLS):
        samples = [r.get(col_name, "") for r in records]
        w = _auto_col_width(col_name, samples, min_w=4.5, max_w=18 if col_name == "KETERANGAN PEKERJAAN" else 12)
        ws.set_column(start_col + i, start_col + i, w)
    ws.set_row(header_row, 30)
    ws.set_row(header_row + 1, 30)

    wb.close()
    out.seek(0)
    return out.getvalue()


def _insert_ttd_image(ws, row: int, col: int, b64: str | None, scale: float = 0.35) -> None:
    if not b64:
        return
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return
    bio = BytesIO(raw)
    ws.insert_image(row, col, "ttd.png", {
        "image_data": bio,
        "x_scale": scale,
        "y_scale": scale,
        "object_position": 1,
    })


def generate_lampiran_excel(
    daily_rows: list[dict],
    unit: str,
    pa: float,
    names: dict[str, str],
    vendor: str,
    type_unit: str = "",
    th_unit: str = "",
    ttd_images: dict[str, str | None] | None = None,
) -> bytes:
    buf = BytesIO()
    wb = Workbook(buf, {"in_memory": True})
    sheet_name = unit[:31] if unit else "Lampiran"
    ws = wb.add_worksheet(sheet_name)

    f_pick = wb.add_format({
        "bold": True, "font_name": "Calibri", "font_size": 10, "bg_color": COLOR_PICK,
    })
    f_title = wb.add_format({
        "bold": True, "align": "center", "font_name": "Calibri", "font_size": 14,
    })
    f_label = wb.add_format({"bold": True, "font_name": "Calibri", "font_size": 10})
    f_head = wb.add_format({
        "bold": True, "border": 1, "font_name": "Calibri", "font_size": 9,
        "align": "center", "valign": "vcenter", "bg_color": COLOR_HEAD_SOFT,
    })
    f_cell = wb.add_format({
        "border": 1, "font_name": "Calibri", "font_size": 8, "align": "center",
    })
    f_num = wb.add_format({
        "border": 1, "font_name": "Calibri", "font_size": 8,
        "align": "center", "num_format": "#,##0.##",
    })
    f_left = wb.add_format({
        "border": 1, "font_name": "Calibri", "font_size": 8, "align": "left",
    })
    f_sub = wb.add_format({
        "bold": True, "border": 1, "font_name": "Calibri", "font_size": 9,
        "bg_color": COLOR_SUBTOTAL, "align": "center", "num_format": "#,##0.##",
    })
    f_sub_lab = wb.add_format({
        "bold": True, "border": 1, "font_name": "Calibri", "font_size": 9,
        "bg_color": COLOR_SUBTOTAL, "align": "left",
    })
    f_nama = wb.add_format({
        "bold": True, "underline": True, "align": "center", "font_name": "Calibri",
    })
    f_center = wb.add_format({"align": "center", "font_name": "Calibri", "font_size": 10})

    # Row 1: PILIH UNIT (cyan)
    ws.write(0, 1, "PILIH UNIT:", f_pick)
    ws.write(0, 2, unit, f_pick)

    ws.merge_range(3, 2, 4, 14, f"DAILY REKAPITULASI PEMAKAIAN UNIT RENTAL {vendor}", f_title)

    ws.write(5, 2, "Type Unit    :", f_label)
    ws.write(5, 3, type_unit or "")
    ws.write(5, 10, "Th Unit:", f_label)
    ws.write(5, 11, th_unit or "")

    ws.write(6, 2, "Code Unit :", f_label)
    ws.write(6, 3, unit)
    ws.write(6, 10, "PA :", f_label)
    ws.write(6, 11, f"{int(round(float(pa or 0)))}%")

    # Headers row 10-11 (0-index 9-10)
    hr = 9
    ws.merge_range(hr, 2, hr + 1, 2, "DATE", f_head)
    ws.merge_range(hr, 3, hr + 1, 3, "SHIFT", f_head)
    ws.merge_range(hr, 4, hr, 8, "Hour meter (HM)", f_head)
    ws.merge_range(hr, 9, hr, 11, "Status (Jam)", f_head)
    ws.merge_range(hr, 12, hr + 1, 12, "AREA KERJA", f_head)
    ws.merge_range(hr, 13, hr + 1, 13, "PEKERJAAN", f_head)
    ws.merge_range(hr, 14, hr + 1, 14, "KETERANGAN", f_head)

    sub_heads = [
        (4, "HM Start"), (5, "HM Stop"), (6, "HM Stop"),
        (7, "HM Not Working"), (8, "HM Working"),
        (9, "BD & No Operator"), (10, "Standby Force Majeure"), (11, "Standby Schedule"),
    ]
    for col, label in sub_heads:
        ws.write(hr + 1, col, label, f_head)

    keys = [
        "DATE", "SHIFT", "HM_START", "HM_STOP", "HM_STOP_ADJ",
        "HM_NOT_WORKING", "HM_WORKING", "BD", "FM", "STBY",
        "AREA", "PEKERJAAN", "KETERANGAN",
    ]
    num_keys = {
        "HM_START", "HM_STOP", "HM_STOP_ADJ", "HM_NOT_WORKING",
        "HM_WORKING", "BD", "FM", "STBY",
    }

    for r_i, row in enumerate(daily_rows):
        excel_r = hr + 2 + r_i
        for c_i, key in enumerate(keys):
            val = row.get(key, row.get(key.replace("HM_WORKING", "WORKING"), ""))
            if key == "HM_WORKING" and (val == "" or val is None):
                val = row.get("WORKING", 0)
            if key == "KETERANGAN" and not val:
                val = row.get("INFORMATION", "")
            cell_c = 2 + c_i
            if key in num_keys:
                try:
                    ws.write(excel_r, cell_c, round(float(val or 0), 2), f_num)
                except (TypeError, ValueError):
                    ws.write(excel_r, cell_c, val or "", f_cell)
            elif key in ("AREA", "PEKERJAAN", "KETERANGAN"):
                ws.write(excel_r, cell_c, val or "", f_left)
            else:
                ws.write(excel_r, cell_c, val if val is not None else "", f_cell)

    # SUBTOTAL yellow
    sub_r = hr + 2 + len(daily_rows)
    ws.merge_range(sub_r, 2, sub_r, 7, "SUBTOTAL", f_sub_lab)
    for key, col in (("HM_WORKING", 8), ("BD", 9), ("FM", 10), ("STBY", 11)):
        total = 0.0
        for row in daily_rows:
            try:
                v = row.get(key, row.get("WORKING") if key == "HM_WORKING" else 0)
                total += float(v or 0)
            except (TypeError, ValueError):
                pass
        ws.write(sub_r, col, int(round(total)), f_sub)

    base = sub_r + 3
    ttd_images = ttd_images or {}
    blocks = [
        (2, "Dibuat Oleh,", names.get("nama_dibuat", ""), names.get("jabatan_dibuat", ""), "dibuat"),
        (9, "Diperiksa Oleh,", names.get("nama_diperiksa", ""), names.get("jabatan_diperiksa", ""), "diperiksa"),
        (14, "Diketahui Oleh,", names.get("nama_diketahui", ""), names.get("jabatan_diketahui", ""), "diketahui"),
    ]
    for col, role, nm, jb, key in blocks:
        ws.write(base, col, role, f_center)
        _insert_ttd_image(ws, base + 1, col, ttd_images.get(key))
        ws.write(base + 4, col, nm, f_nama)
        ws.write(base + 5, col, jb, f_center)

    lamp_labels = [
        "DATE", "SHIFT", "HM Start", "HM Stop", "HM Stop",
        "HM Not Working", "HM Working", "BD & No Operator",
        "Standby Force Majeure", "Standby Schedule",
        "AREA KERJA", "PEKERJAAN", "KETERANGAN",
    ]
    for c_i, label in enumerate(lamp_labels):
        key = keys[c_i]
        samples = [r.get(key, "") for r in daily_rows]
        if key == "KETERANGAN":
            samples = [r.get("KETERANGAN") or r.get("INFORMATION") or "" for r in daily_rows]
        max_w = 18 if key in ("AREA", "PEKERJAAN", "KETERANGAN") else 11
        ws.set_column(2 + c_i, 2 + c_i, _auto_col_width(label, samples, min_w=4.5, max_w=max_w))
    ws.set_row(hr, 28)
    ws.set_row(hr + 1, 30)

    wb.close()
    buf.seek(0)
    return buf.getvalue()
