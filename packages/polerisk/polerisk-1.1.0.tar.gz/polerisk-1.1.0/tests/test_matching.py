import numpy as np
import pandas as pd
import pytest
from pathlib import Path

import soilmoisture.core.matching as matching


def test_get_morning_measurements_basic():
    times = ["00:29", "00:30", "01:15", "02:30", "02:31"]
    sm = [0.1, 0.2, 0.3, 0.4, 0.5]
    morning_sm, morning_times = matching._get_morning_measurements(
        times, sm, "20200101"
    )
    assert morning_times == ["00:30", "01:15", "02:30"]
    np.testing.assert_allclose(morning_sm, [0.2, 0.3, 0.4])


def test_convert_to_local_time_filters_invalid_and_uses_utc2local(monkeypatch):
    # Build DataFrame similar to _read_insitu_data output
    df = pd.DataFrame(
        {
            "utc_date": ["20200101", "20200101", "20200102"],
            "utc_time": ["12:00", "01:00", "23:30"],
            "lat": [40.0, np.nan, 41.0],
            "lon": [-105.0, -105.0, np.nan],
            "sm": [0.2, 0.3, 0.4],
        }
    )

    # Monkeypatch utc2local imported in module to fixed mapping
    calls = []

    def fake_utc2local(lon, utc_date, utc_time):
        calls.append((lon, utc_date, utc_time))
        return (
            ("20200101", "05:00") if utc_date == "20200101" else ("20200102", "18:30")
        )

    monkeypatch.setattr(matching, "utc2local", fake_utc2local)

    local_dates, local_times, local_sm = matching._convert_to_local_time(df)

    # second and third rows filtered due to NaNs; only first row remains
    assert local_dates == ["20200101"]
    assert local_times == ["05:00"]
    np.testing.assert_allclose(local_sm, [0.2])
    # utc2local called once for the valid row
    assert calls == [(-105.0, "20200101", "12:00")]


def test_match_insitu_with_lprm_end_to_end(tmp_path, monkeypatch):
    # Create a minimal in-situ whitespace-delimited file matching expected columns
    # Columns in matching._read_insitu_data: utc_date, utc_time, d3..d7, lat, lon, d10..d12, sm, f1, f2
    rows = [
        # date1: two times, one in morning window, one outside
        "20200101 01:00 0 0 0 0 0 40.0 -105.0 0 0 0 0.20 0 0",
        "20200101 10:00 0 0 0 0 0 40.0 -105.0 0 0 0 0.25 0 0",
        # date2: two morning times
        "20200102 00:45 0 0 0 0 0 40.0 -105.0 0 0 0 0.30 0 0",
        "20200102 02:15 0 0 0 0 0 40.0 -105.0 0 0 0 0.40 0 0",
        # date3: no morning time -> should be skipped
        "20200103 15:00 0 0 0 0 0 40.0 -105.0 0 0 0 0.50 0 0",
    ]
    insitu_path = tmp_path / "insitu.stm"
    insitu_path.write_text("\n".join(rows))

    # Monkeypatch utc2local to map UTC to local seamlessly (no date/time change)
    monkeypatch.setattr(matching, "utc2local", lambda lon, d, t: (d, t))

    # Monkeypatch get_lprm_des used via local import in function
    # match_insitu_with_lprm does: from . import get_lprm_des (i.e., soilmoisture.core.get_lprm_des)
    def fake_get_lprm_des(date, lat, lon, lat_grid, lon_grid):
        # return distinct values per date to assert mapping
        return {"20200101": 1.0, "20200102": 2.0}.get(date, np.nan)

    import soilmoisture.core as core_pkg

    monkeypatch.setattr(core_pkg, "get_lprm_des", fake_get_lprm_des)

    in_situ_series, satellite_series, result_dates = matching.match_insitu_with_lprm(
        insitu_path
    )

    # date1: morning window only includes 01:00 -> avg 0.20
    # date2: avg of 00:45 and 02:15 -> (0.30 + 0.40)/2 = 0.35
    np.testing.assert_allclose(in_situ_series, [0.20, 0.35])
    np.testing.assert_allclose(satellite_series, [1.0, 2.0])
    assert result_dates == ["20200101", "20200102"]
