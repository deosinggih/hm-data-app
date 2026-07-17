"""Port dari ba-hm-monitoring/ba_app/data_processor.py (tanpa Streamlit)."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from app.config import (
    FM_KEYS,
    JAM_PER_SHIFT,
    MAX_STBY_PER_SHIFT,
    POT_Z_EXCLUDE_KEYWORDS,
)


def _pick_col(df: pd.DataFrame, *candidates: str) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _apply_res(working: float, fm: float) -> tuple[float, float]:
    w = round(working, 2)
    fm = round(fm, 2)
    stby = min(MAX_STBY_PER_SHIFT, round(max(0, JAM_PER_SHIFT - w - fm), 2))
    if fm > 0 and (fm + w) > JAM_PER_SHIFT:
        bd = round(max(0, JAM_PER_SHIFT - w), 2)
    else:
        bd = round(max(0, JAM_PER_SHIFT - w - fm - stby), 2)
    return bd, stby


def process_core_data(
    df_hm_raw: pd.DataFrame,
    df_status_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_hm = df_hm_raw.copy()
    df_status = df_status_raw.copy()

    for df in [df_hm, df_status]:
        date_col = "DATE" if "DATE" in df.columns else "TANGGAL"
        if date_col not in df.columns and "date" in df.columns:
            date_col = "date"
        df["DATE_CLEAN"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
        shift_col = "SHIFT" if "SHIFT" in df.columns else "shift"
        df["SHIFT_NUM"] = (
            df[shift_col]
            .apply(lambda x: re.findall(r"\d+", str(x))[0] if re.findall(r"\d+", str(x)) else "0")
            .astype(int)
        )
        df.dropna(subset=["DATE_CLEAN"], inplace=True)

    if "CODE UNIT" not in df_hm.columns and "code_unit" in df_hm.columns:
        df_hm["CODE UNIT"] = df_hm["code_unit"]
    if "VENDOR" not in df_hm.columns and "vendor" in df_hm.columns:
        df_hm["VENDOR"] = df_hm["vendor"]
    if "INFORMATION" not in df_hm.columns and "information" in df_hm.columns:
        df_hm["INFORMATION"] = df_hm["information"]

    if "CODE UNIT" not in df_status.columns and "code_unit" in df_status.columns:
        df_status["CODE UNIT"] = df_status["code_unit"]

    df_hm = df_hm.sort_values(["CODE UNIT", "DATE_CLEAN", "SHIFT_NUM"]).reset_index(drop=True)

    start_col = _pick_col(df_hm, "HM START", "hm_start", "HOURS START")
    stop_col = _pick_col(df_hm, "HM STOP", "hm_stop", "HOURS STOP")
    if not start_col or not stop_col:
        raise KeyError("HM START / HM STOP required")

    df_hm["START_VAL"] = pd.to_numeric(df_hm[start_col], errors="coerce").fillna(0)
    df_hm["STOP_VAL"] = pd.to_numeric(df_hm[stop_col], errors="coerce").fillna(0)
    wk_col = _pick_col(df_hm, "AMOUNT (HM)", "amount_hm", "WORKING") or "AMOUNT (HM)"
    if wk_col not in df_hm.columns:
        df_hm["WORKING_VAL"] = df_hm["STOP_VAL"] - df_hm["START_VAL"]
    else:
        df_hm["WORKING_VAL"] = pd.to_numeric(df_hm[wk_col], errors="coerce").fillna(0)

    df_hm["PREV_STOP"] = df_hm.groupby("CODE UNIT")["STOP_VAL"].shift(1)
    df_hm["DIFF_V"] = (df_hm["START_VAL"] - df_hm["PREV_STOP"]).fillna(0)
    df_hm["DIFF_V"] = df_hm["DIFF_V"].apply(lambda x: x if 0 < x < 500 else 0)

    def _get_pot_z(row) -> float:
        v = row["DIFF_V"]
        info = str(row.get("INFORMATION", "")).strip().upper()
        if any(kw in info for kw in POT_Z_EXCLUDE_KEYWORDS):
            return 0.0
        return v if v > 0 else 0.0

    df_hm["POT_Z"] = df_hm.apply(_get_pot_z, axis=1)

    hm_daily = (
        df_hm.groupby(["VENDOR", "CODE UNIT", "DATE_CLEAN", "SHIFT_NUM"])
        .agg(WORKING_VAL=("WORKING_VAL", "sum"), DIFF_V=("DIFF_V", "sum"), POT_Z=("POT_Z", "sum"))
        .reset_index()
    )

    jam_col = next((c for c in df_status.columns if "JAM" in str(c).upper() or c == "jam"), "jam")
    df_status["JAM_VAL"] = pd.to_numeric(df_status[jam_col], errors="coerce").fillna(0)
    cat_col = next(
        (c for c in df_status.columns if "ITEM" in str(c).upper() or "KATEGORI" in str(c).upper()
         or c in ("item_category", "category")),
        "item_category",
    )
    # Prefer item_category for FM; fallback category
    if "item_category" in df_status.columns:
        cat_series = df_status["item_category"]
    else:
        cat_series = df_status[cat_col]
    df_status["IS_FM"] = cat_series.apply(lambda x: any(k in str(x).upper() for k in FM_KEYS))
    df_status["JAM_FM"] = np.where(df_status["IS_FM"], df_status["JAM_VAL"], 0)

    fm_daily = (
        df_status.groupby(["CODE UNIT", "DATE_CLEAN", "SHIFT_NUM"])["JAM_FM"]
        .sum()
        .reset_index()
    )

    df_merged_base = (
        pd.merge(hm_daily, fm_daily, on=["CODE UNIT", "DATE_CLEAN", "SHIFT_NUM"], how="left")
        .fillna(0)
    )
    bd_stby = df_merged_base.apply(
        lambda r: pd.Series(_apply_res(r["WORKING_VAL"], r["JAM_FM"]), index=["BD", "STBY"]),
        axis=1,
    )
    df_merged_base[["BD", "STBY"]] = bd_stby
    df_merged_base["TGL_LABEL"] = (
        df_merged_base["DATE_CLEAN"].apply(lambda x: x.strftime("%d"))
        + " S"
        + df_merged_base["SHIFT_NUM"].astype(str)
    )
    return df_hm, df_status, df_merged_base


def aggregate_pa(df_merged: pd.DataFrame) -> pd.DataFrame:
    df = df_merged.copy()
    df["TOTAL_AVAIL_HR"] = JAM_PER_SHIFT
    agg = (
        df.groupby(["VENDOR", "CODE UNIT"])
        .agg(TOTAL_AVAIL_HR=("TOTAL_AVAIL_HR", "sum"), BD=("BD", "sum"))
        .reset_index()
    )
    agg["PA_PERCENT"] = (
        ((agg["TOTAL_AVAIL_HR"] - agg["BD"]) / agg["TOTAL_AVAIL_HR"]) * 100
    ).round(2)
    return agg


def build_pa_rekap(df_merged: pd.DataFrame, df_po_master: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df_merged.copy()
    df["TOTAL_AVAIL_HR"] = JAM_PER_SHIFT
    recap = (
        df.groupby(["VENDOR", "CODE UNIT"])
        .agg(
            JAM_TERSEDIA=("TOTAL_AVAIL_HR", "sum"),
            WORKING=("WORKING_VAL", "sum"),
            BD=("BD", "sum"),
            FM=("JAM_FM", "sum"),
            STBY=("STBY", "sum"),
            POT_Z=("POT_Z", "sum"),
            TOTAL_SHIFT=("SHIFT_NUM", "count"),
        )
        .reset_index()
    )
    for col in ("JAM_TERSEDIA", "WORKING", "BD", "FM", "STBY", "POT_Z"):
        recap[col] = recap[col].round(2)
    recap["PA (%)"] = (
        ((recap["JAM_TERSEDIA"] - recap["BD"]) / recap["JAM_TERSEDIA"]) * 100
    ).round(2)

    if df_po_master is not None and not df_po_master.empty:
        po = df_po_master.copy()
        if "code_unit_mcr" in po.columns and "CODE UNIT MCR" not in po.columns:
            po["CODE UNIT MCR"] = po["code_unit_mcr"]
        if "po_number" in po.columns:
            po["PO NUMBER"] = po["po_number"]
        if "equipment" in po.columns:
            po["EQUIPMENT"] = po["equipment"]
        if "year" in po.columns:
            po["YEAR"] = po["year"]
        if "periode_str" in po.columns:
            po["PERIODE_STR"] = po["periode_str"]
        po_cols = [c for c in ["CODE UNIT MCR", "PO NUMBER", "EQUIPMENT", "YEAR", "PERIODE_STR"] if c in po.columns]
        if po_cols:
            recap = recap.merge(po[po_cols], left_on="CODE UNIT", right_on="CODE UNIT MCR", how="left")
            recap.drop(columns=["CODE UNIT MCR"], errors="ignore", inplace=True)
    return recap


def build_vendor_summary(recap: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for vendor, grp in recap.groupby("VENDOR"):
        jam = grp["JAM_TERSEDIA"].sum()
        bd = grp["BD"].sum()
        pa = round(((jam - bd) / jam) * 100, 2) if jam > 0 else 0.0
        rows.append({
            "VENDOR": vendor,
            "JUMLAH UNIT": len(grp),
            "PA RATA-RATA (%)": pa,
            "TOTAL JAM TERSEDIA": round(float(jam), 2),
            "TOTAL WORKING": round(float(grp["WORKING"].sum()), 2),
            "TOTAL BD": round(float(bd), 2),
            "TOTAL FM": round(float(grp["FM"].sum()), 2),
            "TOTAL STBY": round(float(grp["STBY"].sum()), 2),
            "UNIT < 80%": int((grp["PA (%)"] < 80).sum()),
            "UNIT > 90%": int((grp["PA (%)"] > 90).sum()),
        })
    return pd.DataFrame(rows)


def build_ba_rows(recap: pd.DataFrame) -> pd.DataFrame:
    """Settlement BA: bonus PA>90%, penalti PA<80% (dari tab_ba)."""
    rows = []
    for i, r in enumerate(recap.to_dict(orient="records"), start=1):
        pa = float(r.get("PA (%)") or 0)
        working = float(r.get("WORKING") or 0)
        bd = float(r.get("BD") or 0)
        pot_z = float(r.get("POT_Z") or 0)
        fm = float(r.get("FM") or 0)
        stby = float(r.get("STBY") or 0)
        bonus = round((pa / 80) * 0.01 * working, 2) if pa > 90 else 0.0
        penalti = round((pa / 80) * 0.075 * bd, 2) if pa < 80 else 0.0
        ditagihkan = round(max(0.0, working + bonus - penalti), 2)
        code = r.get("CODE UNIT") or ""
        rows.append({
            "No": i,
            "PO Numb.": r.get("PO NUMBER") or "",
            "Periode PO": r.get("PERIODE_STR") or "",
            "Type Alat": r.get("EQUIPMENT") or "",
            "No Unit": str(code)[-3:] if code else "",
            "Tahun Unit": r.get("YEAR") or "",
            "PA Unit": round(pa / 100.0, 4),
            "Total HM Sebelum Dipotong": round(working + pot_z, 2),
            "Total Pemotongan HM": round(pot_z, 2),
            "BD & No Operator": round(bd, 2),
            "Standby Force Majeure": round(fm, 2),
            "Standby Schedule": round(stby, 2),
            "TOTAL HM": round(working, 2),
            "PA<80%": penalti,
            "PA>90%": bonus,
            "HM Yang Ditagihkan": ditagihkan,
            "KETERANGAN PEKERJAAN": "",
            "CODE UNIT": code,
            "VENDOR": r.get("VENDOR") or "",
        })
    return pd.DataFrame(rows)