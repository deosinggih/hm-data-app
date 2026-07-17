"""Parity rumus 2 kolom HM Stop + HM Not Working vs angka Keterangan."""

from app.services.lampiran_hm import (
    apply_lampiran_hm_stop_adj,
    hm_gap_not_working,
    hm_stop_adj,
)
from app.services.hm_row_calc import information


def test_hm_stop_adj_gap_uses_next_start():
    assert hm_stop_adj(110, 112) == 112


def test_hm_stop_adj_reset_keeps_stop():
    assert hm_stop_adj(110, 50) == 110


def test_hm_stop_adj_equal_uses_next():
    assert hm_stop_adj(110, 110) == 110


def test_hm_stop_adj_last_row_empty_next():
    assert hm_stop_adj(110, None) == 110
    assert hm_stop_adj(0, None) == 0


def test_not_working_equals_keterangan_number():
    # gap 2 → INFORMATION "2.00 …", HM Not Working harus 2
    stop, nxt = 110.0, 112.0
    gap = hm_gap_not_working(stop, nxt)
    assert gap == 2.0
    assert information(gap, "HM Dipotong Report MCR").startswith("2.00")


def test_not_working_zero_when_reset_or_last():
    assert hm_gap_not_working(110, 50) == 0.0
    assert hm_gap_not_working(110, None) == 0.0


def test_apply_not_working_matches_info_gap():
    rows = [
        {"HM_START": 100, "HM_STOP": 110, "HM_WORKING": 8, "HM_STOP_ADJ": 0, "HM_NOT_WORKING": 0},
        {"HM_START": 112, "HM_STOP": 120, "HM_WORKING": 8, "HM_STOP_ADJ": 0, "HM_NOT_WORKING": 0},
    ]
    apply_lampiran_hm_stop_adj(rows)
    assert rows[0]["HM_STOP_ADJ"] == 112
    assert rows[0]["HM_NOT_WORKING"] == 2.0  # = angka di Keterangan
    assert rows[1]["HM_STOP_ADJ"] == 120
    assert rows[1]["HM_NOT_WORKING"] == 0.0  # baris terakhir


if __name__ == "__main__":
    test_hm_stop_adj_gap_uses_next_start()
    test_hm_stop_adj_reset_keeps_stop()
    test_hm_stop_adj_equal_uses_next()
    test_hm_stop_adj_last_row_empty_next()
    test_not_working_equals_keterangan_number()
    test_not_working_zero_when_reset_or_last()
    test_apply_not_working_matches_info_gap()
    print("ok")
