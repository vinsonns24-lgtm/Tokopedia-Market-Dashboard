import pytest

from src.tampilan import angka, desimal, persen, rupiah


@pytest.mark.parametrize("nilai, digit, harapan", [
    (0.9812, 1, "98,1%"),
    (0.6291, 0, "63%"),
    (0.024, 1, "2,4%"),
    (1.0, 0, "100%"),
])
def test_persen(nilai, digit, harapan):
    assert persen(nilai, digit) == harapan


def test_desimal():
    assert desimal(0.5672) == "0,57"
    assert desimal(1.35, 1) == "1,4"


def test_ribuan_memakai_titik():
    assert angka(29068) == "29.068"
    assert rupiah(302500) == "Rp302.500"
