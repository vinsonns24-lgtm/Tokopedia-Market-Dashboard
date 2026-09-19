import pandas as pd

from src import opportunity, sensitivity


def test_skor_dasar_sama_dengan_dashboard(listings_sintetis):
    # Uji sensitivitas hanya bermakna kalau versi dasarnya persis versi dashboard.
    dashboard = opportunity.beri_skor(opportunity.agregasi_segmen(listings_sintetis))
    dasar = sensitivity.skor(listings_sintetis).reset_index()
    pd.testing.assert_series_equal(dasar["skor_peluang"], dashboard["skor_peluang"])


def test_bootstrap_bisa_diulang_dengan_seed_yang_sama(listings_sintetis):
    a = sensitivity.bootstrap(listings_sintetis, n=5, seed=1)
    b = sensitivity.bootstrap(listings_sintetis, n=5, seed=1)

    pd.testing.assert_frame_equal(a, b)
    assert a.shape == (len(sensitivity.skor(listings_sintetis)), 5)


def test_ringkasan_bootstrap_berupa_porsi(listings_sintetis):
    ringkas = sensitivity.ringkas_bootstrap(
        listings_sintetis, sensitivity.bootstrap(listings_sintetis, n=5)
    )
    for kolom in ["porsi_top1", "porsi_top5", "porsi_top10"]:
        assert ringkas[kolom].between(0, 1).all()
    assert (ringkas["porsi_top1"] <= ringkas["porsi_top5"]).all()
