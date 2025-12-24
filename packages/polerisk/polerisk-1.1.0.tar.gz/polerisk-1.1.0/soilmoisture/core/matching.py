"""
Core functionality for matching in-situ and satellite soil moisture data.

This module provides functions for matching in-situ soil moisture measurements
with satellite-derived soil moisture data from AMSR2 LPRM.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from ..utils.time_utils import utc2local


def _read_insitu_data(in_situ_path: Path) -> pd.DataFrame:
    """
    Read and preprocess in-situ soil moisture data from a file.

    Args:
        in_situ_path: Path to the in-situ data file.

    Returns:
        A DataFrame containing the processed in-situ data.

    Raises:
        FileNotFoundError: If the specified in_situ_path does not exist.
        pd.errors.EmptyDataError: If the input file is empty.
    """
    column_names = [
        "utc_date",
        "utc_time",
        "d3",
        "d4",
        "d5",
        "d6",
        "d7",
        "lat",
        "lon",
        "d10",
        "d11",
        "d12",
        "sm",
        "f1",
        "f2",
    ]

    try:
        df = pd.read_csv(
            in_situ_path,
            delim_whitespace=True,
            header=None,
            names=column_names,
            na_values=[-9999, -9999.0, "-9999", "-9999.0"],
            dtype={"utc_date": str, "utc_time": str},
        )

        # Convert date and time to datetime
        df["datetime_utc"] = pd.to_datetime(
            df["utc_date"] + " " + df["utc_time"], format="%Y%m%d %H:%M"
        )

        return df

    except Exception as e:
        logging.error(f"Error reading in-situ data from {in_situ_path}: {e}")
        raise


def _convert_to_local_time(
    data: pd.DataFrame,
) -> Tuple[List[str], List[str], List[float]]:
    """
    Convert UTC times to local times and filter valid soil moisture measurements.

    Args:
        data: DataFrame containing in-situ measurements.

    Returns:
        A tuple containing three lists:
            - local_dates: List of local dates in 'YYYYMMDD' format
            - local_times: List of local times in 'HH:MM' format
            - local_sm: List of soil moisture values
    """
    local_dates = []
    local_times = []
    local_sm = []

    for _, row in data.iterrows():
        try:
            lat = row["lat"]
            lon = row["lon"]
            utc_date = row["utc_date"]
            utc_time = row["utc_time"]
            sm = row["sm"]

            # Skip rows with missing data
            if pd.isna(lat) or pd.isna(lon) or pd.isna(sm):
                continue

            # Convert to local time
            local_date, local_time = utc2local(lon, utc_date, utc_time)

            local_dates.append(local_date)
            local_times.append(local_time)
            local_sm.append(sm)

        except Exception as e:
            logging.warning(f"Error processing row {_}: {e}")
            continue

    return local_dates, local_times, local_sm


def _get_morning_measurements(
    times: List[str], sm_values: List[float], date: str
) -> Tuple[List[float], List[str]]:
    """
    Extract soil moisture measurements within the morning time window (00:30-02:30).

    Args:
        times: List of time strings in 'HH:MM' format
        sm_values: List of soil moisture values
        date: Date string for logging

    Returns:
        A tuple containing:
            - morning_sm: Soil moisture values within the morning window
            - morning_times: Corresponding times within the morning window
    """
    morning_sm = []
    morning_times = []

    for time, sm in zip(times, sm_values):
        try:
            hour, minute = map(int, time.split(":"))
            # Convert to minutes since midnight
            minutes_since_midnight = hour * 60 + minute

            # Check if time is between 00:30 and 02:30
            if 30 <= minutes_since_midnight <= 150:  # 00:30 to 02:30
                morning_sm.append(sm)
                morning_times.append(time)

        except Exception as e:
            logging.warning(f"Error processing time {time}: {e}")
            continue

    if not morning_sm:
        logging.warning(f"No morning measurements found for date {date}")

    return morning_sm, morning_times


def match_insitu_with_lprm(
    in_situ_path: Path,
    lat_lprm: Optional[np.ndarray] = None,
    lon_lprm: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Match in-situ soil moisture measurements with satellite data.

    This is the main function that coordinates the entire processing pipeline.

    Args:
        in_situ_path: Path to the in-situ data file.
        lat_lprm: 1D array of latitude values from the LPRM grid.
        lon_lprm: 1D array of longitude values from the LPRM grid.

    Returns:
        A tuple containing three numpy arrays:
            - in_situ_series: Array of in-situ soil moisture values
            - satellite_series: Array of corresponding satellite soil moisture values
            - result_dates: Array of dates corresponding to the measurements
    """
    from . import get_lprm_des  # Import here to avoid circular imports

    # Read and preprocess in-situ data
    in_situ_data = _read_insitu_data(in_situ_path)

    # Convert to local time
    local_dates, local_times, local_sm = _convert_to_local_time(in_situ_data)

    # Group by date
    unique_dates = sorted(set(local_dates))

    # Initialize result arrays
    in_situ_series = []
    satellite_series = []
    result_dates = []

    no_morning_data_dates = []
    missing_satellite_dates = []

    # Process each date
    for date in unique_dates:
        try:
            # Get all measurements for this date
            date_mask = [d == date for d in local_dates]
            times = [t for t, m in zip(local_times, date_mask) if m]
            sm_values = [s for s, m in zip(local_sm, date_mask) if m]

            # Get morning measurements (00:30-02:30)
            morning_sm, morning_times = _get_morning_measurements(
                times, sm_values, date
            )

            if not morning_sm:
                no_morning_data_dates.append(date)
                continue

            # Use the average of morning measurements
            avg_sm = np.mean(morning_sm)

            # Get corresponding satellite data
            # For now, we'll just use the first measurement's location
            # In a real implementation, you might want to handle this differently
            idx = date_mask.index(True)
            lat = in_situ_data.iloc[idx]["lat"]
            lon = in_situ_data.iloc[idx]["lon"]

            # Get satellite data
            sat_sm = get_lprm_des(date, lat, lon, lat_lprm, lon_lprm)

            if np.isnan(sat_sm):
                missing_satellite_dates.append(date)
                continue

            # Add to results
            in_situ_series.append(avg_sm)
            satellite_series.append(sat_sm)
            result_dates.append(date)

        except Exception as e:
            logging.error(f"Error processing date {date}: {e}")
            continue

    # Log processing summary
    _log_processing_summary(
        unique_dates, no_morning_data_dates, missing_satellite_dates, result_dates
    )

    return np.array(in_situ_series), np.array(satellite_series), result_dates


def _log_processing_summary(
    unique_dates: List[str],
    no_morning_data_dates: List[str],
    missing_satellite_dates: List[str],
    processed_dates: List[str],
) -> None:
    """
    Log a summary of the data processing results.

    Args:
        unique_dates: List of all unique dates in the dataset
        no_morning_data_dates: Dates with no valid morning measurements
        missing_satellite_dates: Dates with missing satellite data
        processed_dates: Dates that were successfully processed
    """
    total_dates = len(unique_dates)
    processed_count = len(processed_dates)
    no_morning_count = len(no_morning_data_dates)
    missing_sat_count = len(missing_satellite_dates)

    logging.info("=" * 80)
    logging.info("PROCESSING SUMMARY")
    logging.info("=" * 80)
    logging.info(f"Total dates in dataset: {total_dates}")
    logging.info(
        f"Successfully processed: {processed_count} ({processed_count/max(1, total_dates):.1%})"
    )
    logging.info(f"No morning data: {no_morning_count}")
    logging.info(f"Missing satellite data: {missing_sat_count}")
    logging.info("-" * 80)

    if no_morning_count > 0:
        logging.info("Dates with no morning data (00:30-02:30):")
        for date in no_morning_data_dates:
            logging.info(f"  {date}")

    if missing_sat_count > 0:
        logging.info("Dates with missing satellite data:")
        for date in missing_satellite_dates:
            logging.info("  %s", date)

    logging.info("=" * 80)
