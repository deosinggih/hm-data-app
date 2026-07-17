"""Parity rumus sheet DATA HM (BA Monitoring Excel)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

import pandas as pd


def queery(d: date, shift: str, code_unit: str) -> str:
    return f"{d}{shift}{code_unit}"


def cn_from_unit(code_unit: str) -> str:
    return str(code_unit)[-3:] if code_unit else ""


def _r2(v: float) -> float:
    return round(float(v), 2)


def amount_hm(hm_start: float, hm_stop: float) -> float | None:
    try:
        return _r2(float(hm_stop) - float(hm_start))
    except (TypeError, ValueError):
        return None


def amount_ew(hours_start: time | None, hours_stop: time | None) -> float:
    """Excel: IF(OR(J="",K=""),0, IF(HOUR(24+K-J)+MINUTE(...)=0,24,...))."""
    if hours_start is None or hours_stop is None:
        return 0.0
    try:
        base = datetime(2000, 1, 1)
        t0 = datetime.combine(base.date(), hours_start)
        t1 = datetime.combine(base.date(), hours_stop)
        delta = (t1 + timedelta(days=1)) - t0  # 24+K-J pattern
        hours = delta.total_seconds() / 3600.0
        # Normalize to [0, 24)
        hours = hours % 24
        if hours == 0:
            return 24.0
        return _r2(hours)
    except Exception:
        return 0.0


def _exp_str(exp) -> str:
    if exp is None:
        return ""
    try:
        import math
        if isinstance(exp, float) and math.isnan(exp):
            return ""
    except Exception:
        pass
    s = str(exp).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return s


def pemotongan_hm(hm_diff_val: float, exp: str | None) -> float:
    """=IF(OR(W="",W="HM Error"),0,V)."""
    exp_s = _exp_str(exp)
    if exp_s == "" or exp_s.lower() == "hm error":
        return 0.0
    return _r2(hm_diff_val) if hm_diff_val else 0.0


def pemotongan_serap(hm_diff_val: float, exp: str | None) -> float:
    """=IF(OR(W="",W="HM Serap Unit",W="HM Error"),0,V)."""
    exp_s = _exp_str(exp).lower()
    if exp_s in ("", "hm error", "hm serap unit"):
        return 0.0
    return _r2(hm_diff_val) if hm_diff_val else 0.0


def information(hm_diff_val: float, exp: str | None) -> str:
    """=IF(OR(V=0), "", ROUND(V,2)&" "&W)."""
    try:
        v = float(hm_diff_val)
    except (TypeError, ValueError):
        return ""
    if v == 0:
        return ""
    exp_s = _exp_str(exp)
    return f"{_r2(v):.2f} {exp_s}".strip()


def validate_row(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        start = float(payload.get("hm_start", 0))
        stop = float(payload.get("hm_stop", 0))
    except (TypeError, ValueError):
        errors.append("HM START dan HM STOP harus angka")
        return errors
    amt = amount_hm(start, stop)
    if amt is None:
        errors.append("AMOUNT (HM) tidak dapat dihitung")
    elif amt < 0:
        errors.append("HM STOP harus ≥ HM START (AMOUNT HM negatif)")
    if not payload.get("date"):
        errors.append("DATE wajib")
    if not payload.get("shift"):
        errors.append("SHIFT wajib")
    if not payload.get("vendor"):
        errors.append("VENDOR wajib")
    if not payload.get("code_unit"):
        errors.append("CODE UNIT wajib")
    return errors


def recompute_dataframe(rows: list[dict[str, Any]], status_df: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    """Sort like Excel by CODE UNIT, DATE, SHIFT then fill derived columns."""
    if not rows:
        return []

    df = pd.DataFrame(rows)
    df["_shift_num"] = df["shift"].astype(str).str.extract(r"(\d+)").fillna("0").astype(int)
    df = df.sort_values(["code_unit", "date", "_shift_num"]).reset_index(drop=True)

    for i, row in df.iterrows():
        df.at[i, "queery"] = queery(row["date"], row["shift"], row["code_unit"])
        df.at[i, "cn"] = cn_from_unit(row["code_unit"])
        amt = amount_hm(row["hm_start"], row["hm_stop"])
        df.at[i, "amount_hm"] = amt
        df.at[i, "amount_ew"] = amount_ew(row.get("hours_start"), row.get("hours_stop"))

    # HM DIFFERENCE = IF(next unit same, ROUND(next START - this STOP, 3), "GANTI UNIT")
    for i in range(len(df)):
        if i + 1 < len(df) and df.at[i + 1, "code_unit"] == df.at[i, "code_unit"]:
            gap = _r2(float(df.at[i + 1, "hm_start"]) - float(df.at[i, "hm_stop"]))
            df.at[i, "hm_difference"] = f"{gap:.2f}"
            diff_val = gap if gap > 0 else 0.0
        else:
            df.at[i, "hm_difference"] = "GANTI UNIT"
            diff_val = 0.0

        exp = df.at[i, "exp_difference"]
        df.at[i, "information"] = information(diff_val, exp)
        df.at[i, "pemotongan_hm"] = pemotongan_hm(diff_val, exp)
        df.at[i, "pemotongan_serap"] = pemotongan_serap(diff_val, exp)

    # HM TODAY = IF(prev date&unit == this, prev AMOUNT + this AMOUNT, "")
    for i in range(len(df)):
        if i == 0:
            df.at[i, "hm_today"] = None
            continue
        prev = df.iloc[i - 1]
        cur = df.iloc[i]
        if prev["date"] == cur["date"] and prev["code_unit"] == cur["code_unit"]:
            a0 = prev["amount_hm"] or 0
            a1 = cur["amount_hm"] or 0
            df.at[i, "hm_today"] = _r2(float(a0) + float(a1))
        else:
            df.at[i, "hm_today"] = None

    # STATUS SUMIFS parity
    if status_df is not None and not status_df.empty:
        for i, row in df.iterrows():
            ewh, stb, bd, hm_pot, rem = sumifs_status(
                status_df, row["date"], row["shift"], row["code_unit"]
            )
            df.at[i, "ewh"] = _r2(ewh)
            df.at[i, "stb"] = _r2(stb)
            df.at[i, "bd"] = _r2(bd)
            df.at[i, "hm_pemotongan_status"] = _r2(hm_pot)
            df.at[i, "remaks"] = rem
    else:
        for col in ("ewh", "stb", "bd", "hm_pemotongan_status"):
            df[col] = None
        df["remaks"] = None

    df = df.drop(columns=["_shift_num"], errors="ignore")
    return df.to_dict(orient="records")


def sumifs_status(
    status_df: pd.DataFrame,
    d: date,
    shift: str,
    code_unit: str,
) -> tuple[float, float, float, float, str | None]:
    """Match Excel SUMIFS on STATUS sheet."""
    sdf = status_df.copy()
    if "date" in sdf.columns:
        sdf["_d"] = pd.to_datetime(sdf["date"], errors="coerce").dt.date
    else:
        return 0.0, 0.0, 0.0, 0.0, None

    mask = (
        (sdf["_d"] == d)
        & (sdf["shift"].astype(str) == str(shift))
        & (sdf["code_unit"].astype(str) == str(code_unit))
    )
    sub = sdf.loc[mask]
    if sub.empty:
        return 0.0, 0.0, 0.0, 0.0, None

    def _sum_cat(cat: str) -> float:
        m = sub["category"].astype(str).str.upper() == cat.upper()
        return float(pd.to_numeric(sub.loc[m, "jam"], errors="coerce").fillna(0).sum())

    ewh = _sum_cat("Working")
    stb = _sum_cat("Standby")
    bd = _sum_cat("Breakdown")
    m_op = sub["item_category"].astype(str).str.contains("UR-Operator Problem", case=False, na=False)
    hm_pot = float(pd.to_numeric(sub.loc[m_op, "jam"], errors="coerce").fillna(0).sum())
    rem = None
    if m_op.any():
        rem = str(sub.loc[m_op, "remarks"].iloc[0] or "") or None
    return ewh, stb, bd, hm_pot, rem