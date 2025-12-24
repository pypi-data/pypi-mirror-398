import numpy as np
import numpy.ma as ma
import pytest

import soilmoisture.core.lprm_utils as lu


class FakeNCVar:
    def __init__(self, arr):
        self._arr = arr

    def __getitem__(self, item):
        return self._arr


class FakeNCDS:
    def __init__(self, variables):
        self.variables = variables

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_LPRMDataLoader_load_netcdf_file_success(tmp_path, monkeypatch):
    loader = lu.LPRMDataLoader()

    vars_dict = {
        "lat": FakeNCVar(np.array([1, 2, 3])),
        "lon": FakeNCVar(np.array([10, 20, 30])),
        "soil_moisture": FakeNCVar(np.array([[1.0, 2.0], [3.0, 4.0]])),
    }

    def fake_dataset(path, mode):
        # ensure path exists check passed
        return FakeNCDS(vars_dict)

    # create dummy file so exists() passes
    f = tmp_path / "file.nc"
    f.write_text("")
    monkeypatch.setattr(lu.nc, "Dataset", fake_dataset)

    data = loader.load_netcdf_file(f)
    assert set(data.keys()) == set(vars_dict.keys())
    np.testing.assert_array_equal(data["lat"], np.array([1, 2, 3]))


def test_LPRMDataLoader_load_netcdf_file_not_found():
    loader = lu.LPRMDataLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_netcdf_file("/non/existent/file.nc")


def test_find_nearest_valid_pixel():
    # shape (time, lat, lon) = (2, 3, 3)
    data = np.array(
        [
            [
                [np.nan, np.nan, np.nan],
                [np.nan, 1.0, np.nan],
                [np.nan, np.nan, np.nan],
            ],
            [
                [np.nan, np.nan, np.nan],
                [np.nan, 2.0, np.nan],
                [np.nan, np.nan, np.nan],
            ],
        ]
    )

    loader = lu.LPRMDataLoader()
    # target is center (1,1) which is valid across time
    ts = loader.find_nearest_valid_pixel(data, 1, 1, search_radius=2)
    np.testing.assert_array_equal(ts, np.array([1.0, 2.0]))

    # make center invalid but neighbor valid
    data[:, 1, 1] = np.nan
    data[:, 1, 2] = [5.0, 6.0]
    ts2 = loader.find_nearest_valid_pixel(data, 1, 1, search_radius=2)
    np.testing.assert_array_equal(ts2, np.array([5.0, 6.0]))

    # all invalid
    data[:, :, :] = np.nan
    ts3 = loader.find_nearest_valid_pixel(data, 1, 1, search_radius=1)
    assert ts3 is None


def test_extract_pixel_data_and_find_grid_index():
    # simple 3x3 grid
    lat_grid = np.array([0.0, 1.0, 2.0])
    lon_grid = np.array([10.0, 11.0, 12.0])
    data = np.arange(2 * 3 * 3).reshape(2, 3, 3)

    ts = lu.extract_pixel_data(data, 1.0, 11.0, lat_grid, lon_grid)
    # row=1, col=1 -> values [4, 13]
    np.testing.assert_array_equal(ts, np.array([4, 13]))

    with pytest.raises(ValueError):
        lu.extract_pixel_data(np.array([1, 2, 3]), 1.0, 11.0, lat_grid, lon_grid)


def test__find_nearest_valid_masked():
    # 2D masked array with center masked, neighbor (1,2) valid with value 3.0
    data = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 3.0],
            [0.0, 0.0, 0.0],
        ]
    )
    mask = np.array(
        [
            [True, True, True],
            [True, True, False],  # only (1,2) is unmasked/valid
            [True, True, True],
        ]
    )
    a = ma.masked_array(data, mask=mask)
    val = lu._find_nearest_valid(a, 1, 1, max_distance=2)
    assert val == 3.0

    # if all masked -> nan
    all_mask = np.ones((3, 3), dtype=bool)
    b = ma.masked_array(np.zeros((3, 3)), mask=all_mask)
    res = lu._find_nearest_valid(b, 1, 1, max_distance=1)
    assert np.isnan(res)
