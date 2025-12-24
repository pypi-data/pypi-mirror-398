import numpy as np
import pandas as pd
import logging
from utc2local import utc2local
from getlprm_des import get_lprm_des

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="processing.log",
    filemode="w",  # Overwrite previous log file
)


def _read_insitu_data(in_situ_path):
    """
    Read and preprocess in-situ soil moisture data from a file.

    Args:
        in_situ_path (str): Path to the in-situ data file. The file should be a
            space-separated text file with specific columns including date, time,
            latitude, longitude, and soil moisture measurements.

    Returns:
        pandas.DataFrame: A DataFrame containing the processed in-situ data with
            columns for UTC date, UTC time, latitude, longitude, and soil moisture.

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

    # Read the data
    data = pd.read_csv(
        in_situ_path,
        delim_whitespace=True,
        header=None,
        names=column_names,
        na_values=["-9999", "NaN", "NA", "N/A", "nan", "null"],
    )

    # Filter out invalid soil moisture values (should be between 0 and 1)
    data["sm"] = data["sm"].where((data["sm"] >= 0) & (data["sm"] <= 1), np.nan)
    return data


def _convert_to_local_time(data):
    """
    Convert UTC times to local times and filter valid soil moisture measurements.

    Args:
        data (pandas.DataFrame): DataFrame containing in-situ measurements with
            columns 'utc_date', 'utc_time', 'lat', 'lon', and 'sm' (soil moisture).

    Returns:
        tuple: A tuple containing three lists:
            - local_dates (list): List of local dates in 'YYYYMMDD' format
            - local_times (list): List of local times in 'HH:MM' format
            - local_sm (list): List of soil moisture values corresponding to the local times
    """
    local_dates, local_times, local_sm = [], [], []
    lon = data["lon"].iloc[0]  # Longitude is constant for all rows
    for _, row in data.iterrows():
        if pd.notna(row["sm"]):
            local_date, local_time = utc2local(
                lon,
                row["utc_date"].replace("-", ""),  # Convert YYYY-MM-DD to YYYYMMDD
                row["utc_time"],
            )
            local_dates.append(local_date)
            local_times.append(local_time)
            local_sm.append(row["sm"])

    return local_dates, local_times, local_sm


def _get_morning_measurements(times, sm_values, date):
    """
    Extract soil moisture measurements within the morning time window (00:30-02:30).

    The function identifies measurements that fall within the specified time window
    and returns the corresponding soil moisture values and times.

    Args:
        times (list): List of time strings in 'HH:MM' format
        sm_values (list): List of soil moisture values corresponding to the times
        date (str): Date string in 'YYYYMMDD' format (used for logging)

    Returns:
        tuple: A tuple containing two lists:
            - morning_sm (list): Soil moisture values within the morning window
            - morning_times (list): Corresponding times within the morning window
    """
    morning_sm, morning_times = [], []

    for time, sm in zip(times, sm_values):
        try:
            hh, mm = map(int, time.split(":"))
            total_minutes = hh * 60 + mm
            if 30 <= total_minutes <= 150:  # 00:30 to 02:30
                morning_sm.append(sm)
                morning_times.append(time)
        except (ValueError, AttributeError):
            logging.warning(f"Invalid time format '{time}' for date {date}")

    return morning_sm, morning_times


def _log_processing_summary(
    unique_dates, no_morning_data_dates, missing_satellite_dates, processed_dates
):
    """
    Log a summary of the data processing results.

    This function generates a detailed log message summarizing the processing
    results, including counts of processed dates, dates with missing morning
    data, and dates with missing satellite data.

    Args:
        unique_dates (list): List of all unique dates in the dataset
        no_morning_data_dates (list): Dates with no valid morning measurements
        missing_satellite_dates (list): Dates with missing satellite data
        processed_dates (list): Dates that were successfully processed
    """
    logging.info("\n=== Processing Summary ===")
    logging.info(f"Total unique dates with in-situ data: {len(unique_dates)}")

    morning_count = len(unique_dates) - len(no_morning_data_dates)
    logging.info(f"Dates with morning measurements: {morning_count}")

    sat_count = len(unique_dates) - len(missing_satellite_dates)
    logging.info(f"Dates with satellite data: {sat_count}")
    logging.info(f"Successfully processed dates: {len(processed_dates)}")

    if no_morning_data_dates:
        logging.info("\n=== Dates with no morning measurements ===")
        for date in sorted(no_morning_data_dates):
            logging.info(f"  {date}")

    if missing_satellite_dates:
        logging.info("\n=== Dates missing satellite data ===")
        for date in sorted(missing_satellite_dates):
            logging.info(f"  {date}")


def match_insitu_with_lprm(in_situ_path):
    """
    Match in-situ soil moisture measurements with satellite data.

    This is the main function that coordinates the entire processing pipeline:
    1. Reads and preprocesses in-situ data
    2. Converts UTC times to local times
    3. Filters measurements to the morning window (00:30-02:30)
    4. Matches in-situ data with satellite measurements
    5. Handles missing data and logs processing results

    Args:
        in_situ_path (str): Path to the in-situ data file. The file should be a
            space-separated text file with columns for date, time, latitude,
            longitude, and soil moisture measurements.

    Returns:
        tuple: A tuple containing three numpy arrays:
            - in_situ_series: Array of in-situ soil moisture values
            - satellite_series: Array of corresponding satellite soil moisture values
            - result_dates: Array of dates corresponding to the measurements

    Example:
        >>> in_situ, satellite, dates = match_insitu_with_lprm('path/to/insitu.txt')
        logger.debug(f"Processed {len(dates)} days of data")

    Notes:
        - Missing satellite data is represented as NaN in the output
        - The function logs detailed processing information to 'processing.log'
    """
    # Read and preprocess the data
    data = _read_insitu_data(in_situ_path)
    lat, lon = data["lat"].iloc[0], data["lon"].iloc[0]
    local_dates, local_times, local_sm = _convert_to_local_time(data)
    # Process data by unique local dates
    unique_dates = sorted(set(local_dates))
    logging.info(f"Found {len(unique_dates)} unique dates with valid in-situ data")
    in_situ_series, satellite_series, result_dates = [], [], []
    missing_satellite_dates, no_morning_data_dates = [], []
    for date in unique_dates:
        # Get all measurements for this date
        date_indices = [i for i, d in enumerate(local_dates) if d == date]
        times = [local_times[i] for i in date_indices]
        sm_values = [local_sm[i] for i in date_indices]

        # Process morning measurements
        morning_sm, morning_times = _get_morning_measurements(times, sm_values, date)

        # Log morning measurement details
        log_msg = (
            f"Date {date}: Found {len(morning_sm)} measurements "
            "in morning window (00:30-02:30)"
        )
        logging.debug(log_msg)
        if morning_times:
            logging.debug(f"  - Times found: {', '.join(morning_times)}")
        else:
            logging.warning(f"No morning measurements found for date {date}")
            no_morning_data_dates.append(date)
            continue

        # Calculate mean of available measurements
        in_situ_value = np.nanmean(morning_sm)
        if np.isnan(in_situ_value):
            logging.warning(f"No valid in-situ data for date {date}")
            continue

        # Get corresponding satellite data
        sat_value = get_lprm_des(date, lat, lon)
        if np.isnan(sat_value):
            logging.warning(
                f"No satellite data available for date {date}, will use NaN"
            )
            missing_satellite_dates.append(date)
            sat_value = np.nan

        # Store results
        in_situ_series.append(in_situ_value)
        satellite_series.append(sat_value)
        result_dates.append(date)

        # Log processing result
        sat_status = "NaN" if np.isnan(sat_value) else f"{sat_value:.4f}"
        logging.info(
            f"Processed date {date}: in-situ={in_situ_value:.4f}, "
            f"satellite={sat_status}"
        )

    # Log final summary
    _log_processing_summary(
        unique_dates, no_morning_data_dates, missing_satellite_dates, result_dates
    )
    return np.array(in_situ_series), np.array(satellite_series), result_dates
