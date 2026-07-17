"""Parity rumus kolom Hour meter di sheet Lampiran (BA Monitoring Excel)."""

from __future__ import annotations


def hm_stop_adj(hm_stop: float, next_hm_start: float | None) -> float:
    """Excel Lampiran col G: =IF(E_next<F_this, F_this, E_next).

    - F (HM Stop #1) = HM STOP dari DATA HM
    - G (HM Stop #2) = stop disesuaikan dengan HM Start baris berikutnya
    - Baris terakhir: E_next kosong → Excel treat sebagai 0
    """
    nxt = 0.0 if next_hm_start is None else float(next_hm_start)
    stop = float(hm_stop or 0)
    return stop if nxt < stop else nxt


def hm_gap_not_working(hm_stop: float, next_hm_start: float | None) -> float:
    """Angka di INFORMATION/Keterangan = max(0, next_start - this_stop).

    Di Excel, saat HM Working = AMOUNT (HM), kolom H (HM Not Working)
    = MAX(0,(G-E)-I) jatuh sama dengan gap ini — angka yang tampil di Keterangan.
    """
    nxt = 0.0 if next_hm_start is None else float(next_hm_start)
    stop = float(hm_stop or 0)
    return max(0.0, nxt - stop)


def apply_lampiran_hm_stop_adj(rows: list[dict]) -> None:
    """Isi HM_STOP_ADJ + HM_NOT_WORKING in-place (parity Excel Lampiran)."""
    for i, row in enumerate(rows):
        next_start = rows[i + 1]["HM_START"] if i + 1 < len(rows) else 0.0
        row["HM_STOP_ADJ"] = round(hm_stop_adj(row["HM_STOP"], next_start), 2)
        # Samakan dengan angka di Keterangan (INFORMATION / HM DIFFERENCE)
        row["HM_NOT_WORKING"] = round(hm_gap_not_working(row["HM_STOP"], next_start), 2)
