"""
Plotting functions for soil moisture analysis.

This module contains functions for creating various visualizations of
soil moisture data, including time series plots, scatter plots, distribution
plots, and geographic maps.
"""

import logging
from pathlib import Path

# Third-party imports
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
import signalplot

# Apply SignalPlot minimalist defaults
signalplot.apply()

logger = logging.getLogger(__name__)


def plot_time_series(df: pd.DataFrame, output_dir: str = "Analysis") -> str:
    """
    Plot time series of in-situ and satellite soil moisture.

    Args:
        df: DataFrame containing soil moisture data with datetime index
        output_dir: Directory to save the output plot

    Returns:
        str: Path to the generated plot file
    """
    output_path = Path(output_dir) / "soil_moisture_time_series.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot in-situ data
    ax.plot(df.index, df["in_situ"], "b-", label="In-situ", linewidth=2)

    # Plot satellite data
    ax.plot(df.index, df["satellite"], "r--", label="Satellite (LPRM)", linewidth=2)

    ax.set_title("Time Series of Soil Moisture", fontsize=14, pad=15)
    ax.set_xlabel("Date")
    ax.set_ylabel("Soil Moisture (m³/m³)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Format x-axis dates
    date_format = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()

    # Save the plot
    fig.savefig(str(output_path), dpi=300, bbox_inches="tight")
    plt.close()

    return str(output_path)


def plot_scatter(df: pd.DataFrame, output_dir: str = "Analysis") -> str:
    """
    Create a scatter plot comparing in-situ and satellite soil moisture.

    Args:
        df: DataFrame containing soil moisture data
        output_dir: Directory to save the output plot

    Returns:
        str: Path to the generated plot file
    """
    output_path = Path(output_dir) / "soil_moisture_scatter.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter out NaN values for the scatter plot
    valid_data = df.dropna(subset=["in_situ", "satellite"])

    if len(valid_data) == 0:
        logger.debug("No valid data points for scatter plot")
        return ""

    # Calculate statistics
    r, _ = stats.pearsonr(valid_data["in_situ"], valid_data["satellite"])
    bias = np.mean(valid_data["satellite"] - valid_data["in_situ"])
    rmse = np.sqrt(np.mean((valid_data["satellite"] - valid_data["in_situ"]) ** 2))
    ubrmse = np.sqrt(
        np.mean(
            (
                (valid_data["satellite"] - valid_data["satellite"].mean())
                - (valid_data["in_situ"] - valid_data["in_situ"].mean())
            )
            ** 2
        )
    )

    # Create scatter plot
    plt.figure(figsize=(8, 8))
    sns.scatterplot(x="in_situ", y="satellite", data=valid_data, alpha=0.6, s=80)

    # Add 1:1 line
    min_val = min(valid_data[["in_situ", "satellite"]].min())
    max_val = max(valid_data[["in_situ", "satellite"]].max())
    plt.plot([min_val, max_val], [min_val, max_val], "k--", alpha=0.5)

    # Add statistics
    stats_text = (
        f"N = {len(valid_data)}\n"
        f"R = {r:.3f}\n"
        f"Bias = {bias:.4f} m³/m³\n"
        f"RMSE = {rmse:.4f} m³/m³\n"
        f"ubRMSE = {ubrmse:.4f} m³/m³"
    )

    plt.text(
        0.05,
        0.95,
        stats_text,
        transform=plt.gca().transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.title("In-situ vs. Satellite Soil Moisture", fontsize=14, pad=15)
    plt.xlabel("In-situ Soil Moisture (m³/m³)", fontsize=12)
    plt.ylabel("Satellite Soil Moisture (m³/m³)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save the plot
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight")
    plt.close()

    return str(output_path)


def plot_distributions(df: pd.DataFrame, output_dir: str = "Analysis") -> str:
    """
    Plot distributions of in-situ and satellite soil moisture.

    Args:
        df: DataFrame containing soil moisture data
        output_dir: Directory to save the output plot

    Returns:
        str: Path to the generated plot file
    """
    output_path = Path(output_dir) / "soil_moisture_distributions.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))

    # Plot histograms
    sns.histplot(
        data=df[["in_situ", "satellite"]].dropna(), kde=True, bins=15, alpha=0.6
    )

    plt.title("Distribution of Soil Moisture Measurements", fontsize=14, pad=15)
    plt.xlabel("Soil Moisture (m³/m³)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.legend(title="Source", labels=["In-situ", "Satellite (LPRM)"])
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save the plot
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight")
    plt.close()

    return str(output_path)


def plot_vegetation_terrain_analysis(
    df: pd.DataFrame, output_dir: str = "Analysis"
) -> str:
    """
    Generate boxplots showing performance across different vegetation and terrain conditions.

    Note: This is a placeholder function. In a real implementation,
    you would need additional data about vegetation and terrain conditions
    for each measurement.

    Args:
        df: DataFrame containing soil moisture data
        output_dir: Directory to save the output plot

    Returns:
        str: Path to the generated plot file, or empty string if no data
    """
    required_cols = ["in_situ", "satellite"]
    if not all(col in df.columns for col in required_cols):
        logging.warning(
            "Missing required columns for vegetation/terrain analysis. "
            "Skipping this visualization."
        )
        return ""

    output_path = Path(output_dir) / "vegetation_terrain_analysis.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot in-situ distribution
    sns.boxplot(data=df, y="in_situ", ax=ax1)
    ax1.set_title("In-situ Soil Moisture Distribution")
    ax1.set_ylabel("Soil Moisture (m³/m³)")

    # Plot satellite distribution
    sns.boxplot(data=df, y="satellite", ax=ax2)
    ax2.set_title("Satellite Soil Moisture Distribution")
    ax2.set_ylabel("Soil Moisture (m³/m³)")

    # Set main title
    plt.suptitle(
        "Soil Moisture Distribution by Data Source\n"
        "(Placeholder: Would be grouped by vegetation/terrain in full implementation)",
        y=1.02,
    )
    plt.tight_layout()

    # Save the plot
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight")
    plt.close()

    return str(output_path)


def plot_site_map(df: pd.DataFrame, output_dir: str = "Analysis") -> str:
    """
    Generate a map showing the location of validation sites.

    Args:
        df: DataFrame containing the data with 'lat' and 'lon' columns
        output_dir: Directory to save the output plot

    Returns:
        str: Path to the generated plot file, or None if failed
    """
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError:
        logging.warning(
            "Cartopy is required for map visualization. "
            "Install with: pip install cartopy"
        )
        return None

    # Check if required columns exist
    if not all(col in df.columns for col in ["lat", "lon"]):
        logging.warning(
            "Missing required columns 'lat' and 'lon' for site map. "
            "Skipping this visualization."
        )
        return None

    # Set up output path
    output_path = Path(output_dir) / "validation_sites_map.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a figure with a map
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Add map features
    ax.add_feature(cfeature.LAND, facecolor="#f0f0f0")
    ax.add_feature(cfeature.OCEAN, facecolor="#e6f3ff")
    ax.add_feature(cfeature.COASTLINE, linewidth=0.7, edgecolor="#555555")
    ax.add_feature(cfeature.BORDERS, linestyle="-", linewidth=0.5, edgecolor="#888888")
    ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor="#b3d9ff")
    ax.add_feature(cfeature.RIVERS)
    ax.stock_img()

    # Plot the sites
    ax.scatter(
        df["lon"],
        df["lat"],
        c="red",
        s=50,
        transform=ccrs.PlateCarree(),
        label="Validation Sites",
    )

    # Add a legend and title
    plt.legend(loc="lower right")
    plt.title("Validation Site Locations")

    # Save the plot
    output_path = Path(output_dir) / "site_location_map.png"
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight")
    plt.close()

    return str(output_path)


def create_dashboard(df: pd.DataFrame, output_dir: str = "Analysis") -> str:
    """
    Create a dashboard with multiple visualizations.

    Args:
        df: DataFrame containing soil moisture data
        output_dir: Directory to save the output files

    Returns:
        str: Path to the generated HTML dashboard
    """
    from jinja2 import Environment, FileSystemLoader

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate all plots
    time_series_path = plot_time_series(df, output_dir)
    scatter_path = plot_scatter(df, output_dir)
    dist_path = plot_distributions(df, output_dir)
    vt_path = plot_vegetation_terrain_analysis(df, output_dir)
    map_path = plot_site_map(df, output_dir)

    # Calculate statistics
    valid_data = df.dropna(subset=["in_situ", "satellite"])
    if len(valid_data) > 0:
        r, _ = stats.pearsonr(valid_data["in_situ"], valid_data["satellite"])
        bias = np.mean(valid_data["satellite"] - valid_data["in_situ"])
        rmse = np.sqrt(np.mean((valid_data["satellite"] - valid_data["in_situ"]) ** 2))
        ubrmse = np.sqrt(
            np.mean(
                (
                    (valid_data["satellite"] - valid_data["satellite"].mean())
                    - (valid_data["in_situ"] - valid_data["in_situ"].mean())
                )
                ** 2
            )
        )
    else:
        r = bias = rmse = ubrmse = float("nan")

    # Create HTML dashboard
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("dashboard_template.html")

    # Prepare data for the template
    context = {
        "num_obs": len(df),
        "num_valid": len(valid_data),
        "correlation": f"{r:.3f}",
        "bias": f"{bias:.4f} m³/m³",
        "rmse": f"{rmse:.4f} m³/m³",
        "ubrmse": f"{ubrmse:.4f} m³/m³",
        "time_series_plot": time_series_path,
        "scatter_plot": scatter_path,
        "distribution_plot": dist_path,
        "vegetation_terrain_plot": vt_path,
        "site_map_plot": map_path,
        "data_available": len(valid_data) > 0,
    }

    # Render the template
    html_content = template.render(**context)

    # Save the HTML file
    dashboard_path = output_path / "soil_moisture_dashboard.html"
    dashboard_path.write_text(html_content, encoding="utf-8")

    return str(dashboard_path)
