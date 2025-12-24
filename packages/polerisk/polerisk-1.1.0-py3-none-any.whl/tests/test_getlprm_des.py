from pathlib import Path
import numpy as np
import pytest

import soilmoisture.core.getlprm_des as mod


class FakeNCVar:
    def __init__(self, arr):
        self._arr = np.array(arr)

    def __getitem__(self, item):
        return self._arr


class FakeDS:
    def __init__(self, variables):
        self.variables = variables

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _install_fake_getpara(monkeypatch, lat, lon, files):
    # Mock ConfigManager.get_parameters instead of the old getpara module
    from soilmoisture.common.config import ConfigManager

    def fake_get_parameters(force_refresh=False):
        return {
            "lat_lprm": np.array(lat),
            "lon_lprm": np.array(lon),
            "file_lprm_des": [Path(p) for p in files],
        }

    monkeypatch.setattr(ConfigManager, "get_parameters", fake_get_parameters)


def test_returns_value_when_matching_date(tmp_path, monkeypatch):
    # Prepare fake parameters and file
    lat = [0.0, 1.0]
    lon = [10.0, 11.0]
    f = tmp_path / "LPRM_20200101_sample.nc"
    f.write_text("")

    _install_fake_getpara(monkeypatch, lat, lon, [str(f)])

    # Mock location to row=1, col=1
    monkeypatch.setattr(mod, "get_location", lambda la, lo, lats, lons: (1, 1))

    # Mock Dataset to return soil_moisture with value 3.14 at (1,1)
    sm = np.zeros((2, 2))
    sm[1, 1] = 3.14

    def fake_dataset(path, mode):
        assert Path(path) == f
        return FakeDS({"soil_moisture": FakeNCVar(sm)})

    monkeypatch.setattr(mod.nc, "Dataset", fake_dataset)

    val = mod.get_lprm_des("20200101", 0.5, 10.5)
    assert val == pytest.approx(3.14)


def test_returns_nan_on_missing_date_or_error(tmp_path, monkeypatch, capsys):
    # File present but date not matching
    f = tmp_path / "LPRM_20200102_sample.nc"
    f.write_text("")

    _install_fake_getpara(monkeypatch, [0.0], [10.0], [str(f)])

    # If date doesn't match, returns nan
    val1 = mod.get_lprm_des("20200101", 0.0, 10.0)
    assert np.isnan(val1)

    # Now date matches but Dataset raises error -> prints and returns nan
    f2 = tmp_path / "LPRM_20200103_sample.nc"
    f2.write_text("")
    _install_fake_getpara(monkeypatch, [0.0], [10.0], [str(f2)])
    monkeypatch.setattr(mod, "get_location", lambda la, lo, lats, lons: (0, 0))

    def boom(path, mode):
        raise KeyError("soil_moisture")

    monkeypatch.setattr(mod.nc, "Dataset", boom)
    val2 = mod.get_lprm_des("20200103", 0.0, 10.0)
    assert np.isnan(val2)
