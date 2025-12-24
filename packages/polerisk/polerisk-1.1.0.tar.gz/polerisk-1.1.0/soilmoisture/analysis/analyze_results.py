#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger(__name__)


def load_results(filepath):
    """Load the match results from the output file."""
    # Read the results file
    df = pd.read_csv(filepath, sep=r'\s+', header=None, 
                    names=['date', 'in_situ', 'satellite'],
                    na_values=['NaN', 'nan', 'NA'])
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    
    # Sort by date
    df = df.sort_values('date')
    
    return df

def plot_results(df, output_file=None):
    """Plot the in-situ and satellite soil moisture data."""
    plt.figure(figsize=(12, 6))
    
    # Plot in-situ data
    plt.plot(df['date'], df['in_situ'], 'b-', label='In-situ', marker='o')
    
    # Plot satellite data
    plt.plot(df['date'], df['satellite'], 'r--', label='Satellite (LPRM)', marker='x')
    
    # Add labels and title
    plt.title('Comparison of In-situ and Satellite Soil Moisture')
    plt.ylabel('Soil Moisture (m³/m³)')
    plt.xlabel('Date')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save or show the plot
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.debug(f"Plot saved to {output_file}")
    else:
        plt.show()

def calculate_statistics(df):
    """Calculate and print basic statistics about the results."""
    logger.debug("\n=== Statistics ===")
    logger.debug(f"Total number of days: {len(df)}")
    logger.debug(f"Days with in-situ data: {df['in_situ'].count()}")
    logger.debug(f"Days with satellite data: {df['satellite'].count()}")
    logger.debug(f"Days with both in-situ and satellite data: {df.dropna(subset=['in_situ', 'satellite']).shape[0]}")
    
    # Calculate correlation (only for days with both measurements)
    valid_data = df.dropna(subset=['in_situ', 'satellite'])
    if len(valid_data) > 1:
        corr = np.corrcoef(valid_data['in_situ'], valid_data['satellite'])[0, 1]
        logger.debug(f"\nCorrelation between in-situ and satellite: {corr:.3f}")
    
    # Basic statistics
    logger.debug("\nIn-situ statistics:")
    logger.debug(df['in_situ'].describe())
    
    logger.debug("\nSatellite statistics:")
    logger.debug(df['satellite'].describe())

def main():
    # Path to the results file
    results_file = os.path.join('Output', 'match_results.txt')
    
    # Load the results
    df = load_results(results_file)
    
    # Print the first few rows
    logger.debug("First few rows of results:")
    logger.debug(df.head())
    
    # Calculate and print statistics
    calculate_statistics(df)
    
    # Create output directory if it doesn't exist
    os.makedirs('Analysis', exist_ok=True)
    
    # Generate and save the plot
    plot_file = os.path.join('Analysis', 'soil_moisture_comparison.png')
    plot_results(df, output_file=plot_file)
    
    # Save the results to a CSV file for further analysis
    csv_file = os.path.join('Analysis', 'soil_moisture_data.csv')
    df.to_csv(csv_file, index=False)
    logger.debug(f"\nResults saved to {csv_file}")

if __name__ == "__main__":
    main()
