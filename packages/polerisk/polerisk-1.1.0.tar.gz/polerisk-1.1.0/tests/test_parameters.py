import os
from pathlib import Path
import numpy as np
import pytest

import soilmoisture.core.parameters as params_mod


class FakeDataset:
    """Minimal fake for netCDF4.Dataset supporting context manager and variables access."""

    def __init__(self, path, mode="r", raise_on_enter=False, lat=None, lon=None):
        self.path = Path(path)
        self.mode = mode
        self._raise_on_enter = raise_on_enter
        # default simple arrays
        self.variables = {
            "lat": np.array([1.0, 2.0, 3.0]) if lat is None else lat,
            "lon": np.array([10.0, 20.0, 30.0]) if lon is None else lon,
        }

    def __enter__(self):
        if self._raise_on_enter:
            raise RuntimeError("Fake open error")
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """
    Create a fake project layout by pointing the module's __file__ up three parents
    to tmp root, so Path(__file__).parent.parent.parent resolves to tmp_path.
    Structure:
    tmp_path/
      Input/
      Output/
    """
    # Point module __file__ so that parent.parent.parent -> tmp_path
    fake_path = tmp_path / "a" / "b" / "c" / "parameters.py"
    fake_path.parent.mkdir(parents=True)
    monkeypatch.setattr(params_mod, "__file__", str(fake_path))

    # Ensure a clean state
    (tmp_path / "Input").mkdir(exist_ok=True)
    # Output will be created by get_parameters

    return tmp_path


def test_no_nc_files_sets_none_and_warns(temp_project, monkeypatch, caplog):
    # No files in Input/LPRM_NetCDF and fallback .nc4 doesn't exist
    caplog.clear()
    para = params_mod.get_parameters()

    # parameters.py uses base_path = Path(__file__).parent.parent.parent -> tmp_path / 'a'
    base = temp_project / "a"
    assert para["lprm_des"] == base / "Input" / "LPRM_NetCDF"
    assert para["lprm_des"].exists()  # directory created
    assert para["size_lprm_des"] == 0
    assert para["file_lprm_des"] == []
    # lat/lon None when nothing to read
    assert para["lat_lprm"] is None
    assert para["lon_lprm"] is None
    # Output dir created
    assert para["out"].exists()
    # Warning logged
    assert any("No NetCDF files found" in rec.message for rec in caplog.records)


def test_reads_first_nc_from_directory(temp_project, monkeypatch):
    # Create two dummy .nc files in Input/LPRM_NetCDF
    base = temp_project / "a"
    lprm_dir = base / "Input" / "LPRM_NetCDF"
    lprm_dir.mkdir(parents=True, exist_ok=True)
    f1 = lprm_dir / "a.nc"
    f2 = lprm_dir / "b.nc"
    f1.write_text("")
    f2.write_text("")

    # Monkeypatch Dataset in module to our FakeDataset returning known arrays
    lat = np.array([0.0, 1.0])
    lon = np.array([10.0, 11.0])

    def fake_dataset(path, mode="r"):
        # Ensure it's opening first file
        assert Path(path) == f1
        return FakeDataset(path, mode, lat=lat, lon=lon)

    monkeypatch.setattr(params_mod, "Dataset", fake_dataset)

    para = params_mod.get_parameters()
    assert para["size_lprm_des"] == 2
    assert [p.name for p in para["file_lprm_des"]] == ["a.nc", "b.nc"]
    # Read arrays populated from first file
    np.testing.assert_array_equal(para["lat_lprm"], lat)
    np.testing.assert_array_equal(para["lon_lprm"], lon)


def test_reads_fallback_nc4_when_no_directory_files(temp_project, monkeypatch):
    # Create fallback nc4 file
    base = temp_project / "a"
    fallback = base / "Input" / "LPRM-AMSR2_L3_D_SOILM3_V001_20150401013507.nc4"
    fallback.parent.mkdir(parents=True, exist_ok=True)
    fallback.write_text("")

    lat = np.array([5.0, 6.0, 7.0])
    lon = np.array([15.0, 16.0, 17.0])

    def fake_dataset(path, mode="r"):
        assert Path(path) == fallback
        return FakeDataset(path, mode, lat=lat, lon=lon)

    monkeypatch.setattr(params_mod, "Dataset", fake_dataset)

    para = params_mod.get_parameters()
    assert para["size_lprm_des"] == 0
    np.testing.assert_array_equal(para["lat_lprm"], lat)
    np.testing.assert_array_equal(para["lon_lprm"], lon)


def test_error_while_reading_sets_none_and_logs(temp_project, monkeypatch, caplog):
    # Put a file in directory so it tries to read, but our Fake raises
    base = temp_project / "a"
    lprm_dir = base / "Input" / "LPRM_NetCDF"
    lprm_dir.mkdir(parents=True, exist_ok=True)
    f1 = lprm_dir / "a.nc"
    f1.write_text("")

    def fake_dataset(path, mode="r"):
        return FakeDataset(path, mode, raise_on_enter=True)

    monkeypatch.setattr(params_mod, "Dataset", fake_dataset)

    caplog.clear()
    para = params_mod.get_parameters()

    assert para["lat_lprm"] is None
    assert para["lon_lprm"] is None
    assert any("Error reading NetCDF file" in rec.message for rec in caplog.records)
