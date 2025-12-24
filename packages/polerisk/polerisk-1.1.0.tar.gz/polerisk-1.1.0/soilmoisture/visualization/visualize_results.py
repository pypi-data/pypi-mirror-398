#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from matplotlib.dates import DateFormatter
import signalplot

# Apply SignalPlot minimalist defaults
signalplot.apply()

import logging
logger = logging.getLogger(__name__)


def load_results(filepath):
    """
    Load the match results from the output file.
    
    Args:
        filepath (str): Path to the results file
        
    Returns:
        pd.DataFrame: DataFrame containing the results with date as datetime index
    """
    # First, read just the first line to check the number of columns
    with open(filepath, 'r') as f:
        first_line = f.readline().strip()
        num_cols = len(first_line.split())
    
    # Define column names based on number of columns
    if num_cols == 3:
        col_names = ['date', 'in_situ', 'satellite']
    elif num_cols >= 5:  # If we have lat/lon data
        col_names = ['date', 'in_situ', 'satellite', 'lat', 'lon']
    else:
        col_names = ['date', 'in_situ', 'satellite']
    
    # Read the data with appropriate column names
    df = pd.read_csv(filepath, sep=r'\s+', header=None, 
                    names=col_names,
                    na_values=['NaN', 'nan', 'NA'])
    
    # Convert date to datetime and sort
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values('date')
    
    return df

def plot_time_series(df, output_dir='Analysis'):
    """Plot time series of in-situ and satellite soil moisture."""
    plt.figure(figsize=(14, 7))
    
    # Plot in-situ data
    plt.plot(df['date'], df['in_situ'], 'b-', label='In-situ', marker='o', markersize=6, 
             linewidth=2, alpha=0.8)
    
    # Plot satellite data
    plt.plot(df['date'], df['satellite'], 'r--', label='Satellite (LPRM)', 
             marker='x', markersize=8, linewidth=2, alpha=0.8)
    
    # Formatting
    plt.title('Time Series of Soil Moisture Measurements\nIn-situ vs. AMSR2 LPRM Satellite Data', 
              fontsize=14, pad=20)
    plt.ylabel('Volumetric Soil Moisture (m³/m³)', fontsize=12)
    plt.xlabel('Date', fontsize=12)
    plt.legend(fontsize=12, loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    
    # Format x-axis dates
    date_form = DateFormatter("%Y-%m-%d")
    plt.gca().xaxis.set_major_formatter(date_form)
    plt.grid(False)

    plt.tight_layout()
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'soil_moisture_time_series.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    return output_file

def plot_scatter(df, output_dir='Analysis'):
    """Create a scatter plot comparing in-situ and satellite soil moisture."""
    # Drop rows with missing values
    valid_data = df.dropna(subset=['in_situ', 'satellite'])
    
    if len(valid_data) < 2:
        logger.debug("Not enough data points for scatter plot")
        return None
    
    plt.figure(figsize=(8, 8))
    
    # Create scatter plot
    sns.regplot(x='in_situ', y='satellite', data=valid_data, 
                scatter_kws={'alpha':0.6, 's':60}, 
                line_kws={'color':'red', 'linewidth':2})
    
    # Add 1:1 line
    min_val = min(valid_data[['in_situ', 'satellite']].min())
    max_val = max(valid_data[['in_situ', 'satellite']].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
    
    # Calculate statistics
    corr, _ = stats.pearsonr(valid_data['in_situ'], valid_data['satellite'])
    bias = np.mean(valid_data['satellite'] - valid_data['in_situ'])
    rmse = np.sqrt(np.mean((valid_data['satellite'] - valid_data['in_situ'])**2))
    
    # Add statistics to plot
    stats_text = (
        f"N = {len(valid_data)}\n"
        f"R = {corr:.3f}\n"
        f"Bias = {bias:.4f} m³/m³\n"
        f"RMSE = {rmse:.4f} m³/m³"
    )
    plt.gca().text(0.05, 0.95, stats_text, transform=plt.gca().transAxes,
                  verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Formatting
    plt.title('In-situ vs. Satellite Soil Moisture', fontsize=14, pad=20)
    plt.xlabel('In-situ Soil Moisture (m³/m³)', fontsize=12)
    plt.ylabel('Satellite Soil Moisture (m³/m³)', fontsize=12)
    plt.grid(False)
    
    # Save the plot
    output_file = os.path.join(output_dir, 'soil_moisture_scatter.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    return output_file

def plot_distributions(df, output_dir='Analysis'):
    """Plot distributions of in-situ and satellite soil moisture."""
    plt.figure(figsize=(12, 6))
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot in-situ distribution
    sns.histplot(df['in_situ'].dropna(), kde=True, color='blue', ax=ax1, bins=10)
    ax1.set_title('In-situ Soil Moisture Distribution', fontsize=12)
    ax1.set_xlabel('Volumetric Soil Moisture (m³/m³)', fontsize=10)
    ax1.set_ylabel('Frequency', fontsize=10)
    
    # Plot satellite distribution
    sns.histplot(df['satellite'].dropna(), kde=True, color='red', ax=ax2, bins=10)
    ax2.set_title('Satellite Soil Moisture Distribution', fontsize=12)
    ax2.set_xlabel('Volumetric Soil Moisture (m³/m³)', fontsize=10)
    ax2.set_ylabel('Frequency', fontsize=10)
    
    # Adjust layout
    plt.tight_layout()
    plt.grid(False)
    
    # Save the plot
    output_file = os.path.join(output_dir, 'soil_moisture_distributions.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    return output_file

def plot_vegetation_terrain_analysis(df, output_dir='Analysis'):
    """
    Generate boxplots showing performance across different vegetation and terrain conditions.
    
    Note: This is a placeholder function. In a real implementation, you would need
    additional data about vegetation and terrain conditions for each measurement.
    """
    # Create sample vegetation and terrain categories for demonstration
    # In a real implementation, you would load this from your data
    np.random.seed(42)  # For reproducible results
    
    # Add synthetic vegetation and terrain data for demonstration
    if len(df) > 0:
        df['vegetation_type'] = np.random.choice(
            ['Forest', 'Grassland', 'Cropland', 'Shrubland'], 
            size=len(df)
        )
        df['terrain_slope'] = pd.cut(
            np.random.uniform(0, 30, size=len(df)), 
            bins=[0, 5, 15, 30],
            labels=['Flat (0-5°)', 'Moderate (5-15°)', 'Steep (>15°)']
        )
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Boxplot by vegetation type
    if 'vegetation_type' in df.columns and 'in_situ' in df.columns and 'satellite' in df.columns:
        # Calculate bias for each measurement
        df['bias'] = df['satellite'] - df['in_situ']
        
        # Plot by vegetation type
        sns.boxplot(
            x='vegetation_type', 
            y='bias', 
            data=df.dropna(subset=['bias', 'vegetation_type']),
            ax=ax1
        )
        ax1.set_title('Bias by Vegetation Type')
        ax1.set_xlabel('Vegetation Type')
        ax1.set_ylabel('Bias (Satellite - In-situ) [m³/m³]')
        ax1.axhline(y=0, color='r', linestyle='--')
        
        # Add sample size to each box
        for i, veg_type in enumerate(df['vegetation_type'].dropna().unique()):
            n = len(df[df['vegetation_type'] == veg_type].dropna(subset=['bias']))
            ax1.text(i, ax1.get_ylim()[1]*0.95, f'n={n}', ha='center', va='top')
    
    # Boxplot by terrain slope
    if 'terrain_slope' in df.columns and 'bias' in df.columns:
        sns.boxplot(
            x='terrain_slope', 
            y='bias', 
            data=df.dropna(subset=['bias', 'terrain_slope']),
            ax=ax2
        )
        ax2.set_title('Bias by Terrain Slope')
        ax2.set_xlabel('Terrain Slope')
        ax2.set_ylabel('Bias (Satellite - In-situ) [m³/m³]')
        ax2.axhline(y=0, color='r', linestyle='--')
        
        # Add sample size to each box
        for i, slope in enumerate(df['terrain_slope'].dropna().unique()):
            n = len(df[df['terrain_slope'] == slope].dropna(subset=['bias']))
            ax2.text(i, ax2.get_ylim()[1]*0.95, f'n={n}', ha='center', va='top')
    
    plt.tight_layout()
    plt.grid(False)
    # Save the plot
    output_file = os.path.join(output_dir, 'vegetation_terrain_analysis.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file if os.path.exists(output_file) else None

def plot_site_map(df, output_dir='Analysis'):
    """
    Generate a map showing the location of validation sites.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data with 'lat' and 'lon' columns
        output_dir (str): Directory to save the output plot
        
    Returns:
        str: Path to the generated plot file, or None if failed
    """
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a figure with a map
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        
        # Add map features with a clean, simple style
        ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
        ax.add_feature(cfeature.OCEAN, facecolor='#e6f3ff')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.7, edgecolor='#555555')
        ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='#888888')
        ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='#b3d9ff')
        
        # Add a subtle grid
        gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.3)
        gl.top_labels = False
        gl.right_labels = False
        
        # Default to US view (since we know the data is from US-Ne2 site)
        ax.set_extent([-125, -66, 24, 50])  # Continental US
        
        # Add a marker for the US-Ne2 site (Mead, Nebraska)
        site_lon, site_lat = -96.4766, 41.1649  # US-Ne2 coordinates
        ax.plot(site_lon, site_lat, 'ro', markersize=10, 
                transform=ccrs.PlateCarree(),
                markeredgecolor='black',
                markeredgewidth=0.5,
                label='US-Ne2 Site (Mead, NE)')
        
        # Add a text label
        ax.text(site_lon + 1, site_lat, 'US-Ne2\nMead, NE',
                transform=ccrs.PlateCarree(),
                fontsize=10,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
        
        # Add a legend
        ax.legend(loc='lower right')
        
        # Add a title
        title = 'Soil Moisture Validation Site: US-Ne2 (Mead, Nebraska)'
        
        # Add a title
        plt.title(title, fontsize=14, pad=20, weight='bold')
        
        # Adjust layout to prevent title overlap
        plt.tight_layout()
        
        # Save the plot
        output_file = os.path.join(output_dir, 'site_location_map.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file if os.path.exists(output_file) else None
        
    except ImportError:
        logger.debug("Cartopy is required for map generation. Install with: pip install cartopy")
        return None

def create_dashboard(df, output_dir='Analysis'):
    """Create a dashboard with multiple visualizations."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate statistics first (before generating plots)
    valid_data = df.dropna(subset=['in_situ', 'satellite']).copy()
    
    # Basic metrics
    corr = valid_data['in_situ'].corr(valid_data['satellite'])
    bias = np.mean(valid_data['satellite'] - valid_data['in_situ'])
    
    # RMSE and unbiased RMSE (ubRMSE)
    diff = valid_data['satellite'] - valid_data['in_situ']
    rmse = np.sqrt(np.mean(diff**2))
    ubrmse = np.sqrt(np.mean((diff - np.mean(diff))**2))  # Remove mean bias before RMSE
    
    # Store metrics in the dataframe for use in plots
    valid_data['bias'] = bias
    valid_data['ubrmse'] = ubrmse
    
    # Generate all plots (pass the valid_data with metrics to plotting functions)
    time_series_plot = plot_time_series(valid_data, output_dir)
    scatter_plot = plot_scatter(valid_data, output_dir)
    dist_plot = plot_distributions(valid_data, output_dir)
    vt_plot = plot_vegetation_terrain_analysis(valid_data, output_dir)
    site_map = plot_site_map(valid_data, output_dir)
    
    # Get current date for the report
    current_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create a simple HTML dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Soil Moisture Analysis Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .plot {{ margin-bottom: 40px; }}
            .plot img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
            h1, h2 {{ color: #2c3e50; }}
            .stats {{ 
                background-color: #f8f9fa; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Soil Moisture Analysis Dashboard</h1>
            <p>Generated on {current_date}</p>
            
            <div class="stats">
                <h3>Dataset Statistics</h3>
                <p>• Total days processed: {len(df)}</p>
                <p>• Days with both in-situ and satellite data: {len(valid_data)}</p>
                <p>• Correlation coefficient (R): {corr:.3f}</p>
                <p>• Mean bias: {bias:.4f} m³/m³</p>
                <p>• Root Mean Square Error (RMSE): {rmse:.4f} m³/m³</p>
                <p>• Unbiased RMSE (ubRMSE): {ubrmse:.4f} m³/m³</p>
                <p>• Number of observations: {len(valid_data)}</p>
            </div>
            
            <div class="plot">
                <h2>Time Series Comparison</h2>
                <img src="{os.path.basename(time_series_plot) if time_series_plot else ''}" alt="Time Series Plot">
            </div>
            
            <div class="plot">
                <h2>Scatter Plot with 1:1 Line</h2>
                <img src="{os.path.basename(scatter_plot) if scatter_plot else ''}" alt="Scatter Plot">
            </div>
            
            <div class="plot">
                <h2>Soil Moisture Distributions</h2>
                <img src="{os.path.basename(dist_plot) if dist_plot else ''}" alt="Distribution Plots">
            </div>
            
            <div class="plot">
                <h2>Performance by Vegetation and Terrain</h2>
                <img src="{os.path.basename(vt_plot) if vt_plot else ''}" alt="Vegetation and Terrain Analysis">
                <p class="note">Note: Synthetic data shown for demonstration. Replace with actual vegetation and terrain data.</p>
            </div>
            
            <div class="plot">
                <h2>Site Location Map</h2>
                <img src="{os.path.basename(site_map) if site_map else ''}" alt="Site Location Map">
                <p class="note">Note: Example site location shown. Replace with actual site coordinates.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save the HTML dashboard
    dashboard_file = os.path.join(output_dir, 'soil_moisture_dashboard.html')
    with open(dashboard_file, 'w') as f:
        f.write(html_content)
    
    return dashboard_file

def main():
    # Path to the results file
    results_file = os.path.join('Output', 'match_results.txt')
    
    # Load the results
    df = load_results(results_file)
    
    # Create the dashboard
    dashboard_file = create_dashboard(df)
    
    logger.info(f"Visualization complete! Dashboard saved to: {dashboard_file}")
    logger.debug(f"Open {dashboard_file} in a web browser to view the results.")

if __name__ == "__main__":
    main()
