from datetime import date, time

from app.services.hm_row_calc import (
    amount_ew,
    amount_hm,
    information,
    pemotongan_hm,
    pemotongan_serap,
    queery,
    recompute_dataframe,
)


def test_amount_hm():
    assert amount_hm(100, 110.5) == 10.5


def test_amount_ew_shift():
    assert amount_ew(time(6, 0), time(18, 0)) == 12.0
    assert amount_ew(time(18, 0), time(6, 0)) == 12.0


def test_pemotongan():
    assert pemotongan_hm(2.5, "") == 0
    assert pemotongan_hm(2.5, "HM Error") == 0
    assert pemotongan_hm(2.5, "Lain") == 2.5
    assert pemotongan_serap(2.5, "HM Serap Unit") == 0


def test_recompute_gap():
    rows = [
        {
            "id": 1,
            "date": date(2026, 7, 1),
            "shift": "Shift 1",
            "vendor": "PT. PIK",
            "code_unit": "PIK-DT-001",
            "hm_start": 100,
            "hm_stop": 110,
            "hours_start": time(6, 0),
            "hours_stop": time(18, 0),
            "exp_difference": "",
        },
        {
            "id": 2,
            "date": date(2026, 7, 1),
            "shift": "Shift 2",
            "vendor": "PT. PIK",
            "code_unit": "PIK-DT-001",
            "hm_start": 112,
            "hm_stop": 120,
            "hours_start": time(18, 0),
            "hours_stop": time(6, 0),
            "exp_difference": "Cek",
        },
    ]
    out = recompute_dataframe(rows)
    assert out[0]["amount_hm"] == 10
    assert out[0]["hm_difference"] == "2.0"
    assert out[0]["pemotongan_hm"] == 0  # exp empty on row0 — wait, gap is on row0 looking at row1 start
    # INFORMATION on row0 uses gap 2.0 and exp of row0 ("")
    assert information(2.0, "") == "2.0"
    assert queery(date(2026, 7, 1), "Shift 1", "PIK-DT-001").endswith("PIK-DT-001")


if __name__ == "__main__":
    test_amount_hm()
    test_amount_ew_shift()
    test_pemotongan()
    test_recompute_gap()
    print("ok")