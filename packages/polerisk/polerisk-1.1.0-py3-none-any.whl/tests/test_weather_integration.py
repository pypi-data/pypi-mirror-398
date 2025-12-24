#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test weather API integration with pole health assessment.
"""

import sys
import os
from datetime import datetime
import pandas as pd
import logging

# Add project root to path
sys.path.append("/Users/k.jones/Documents/moisture")

from soilmoisture.weather import (
    OpenWeatherMapProvider,
    WeatherRiskAssessment,
    WeatherConditions,
    WeatherForecast,
    WeatherAlert,
)

logger = logging.getLogger(__name__)


def test_weather_integration():
    """Test weather API integration."""

    logger.debug(" TESTING WEATHER API INTEGRATION")
    logger.debug("=" * 50)

    # Initialize weather provider (will use mock data without API key)
    weather_provider = OpenWeatherMapProvider()
    risk_assessor = WeatherRiskAssessment(weather_provider)

    # Test locations (using our sample pole locations)
    test_locations = [
        (40.7128, -74.0060, "P001"),  # New York area
        (40.7580, -73.9855, "P002"),  # Manhattan
        (40.6782, -73.9442, "P003"),  # Brooklyn
    ]

    logger.debug("\n TESTING WEATHER DATA RETRIEVAL:")
    logger.debug("-" * 40)

    weather_data = []

    for lat, lon, pole_id in test_locations:
        logger.debug(f"\nPole {pole_id} ({lat:.4f}, {lon:.4f}):")

        # Test current conditions
        conditions = weather_provider.get_current_conditions(lat, lon)
        if conditions:
            logger.debug(
                f"  Current: {conditions.temperature_c:.1f}°C, {conditions.humidity_percent:.0f}% humidity"
            )
            logger.debug(
                f"  Wind: {conditions.wind_speed_mph:.1f} mph @ {conditions.wind_direction_deg:.0f}°"
            )
            logger.debug(f"  Conditions: {conditions.weather_description}")

            weather_data.append(
                {
                    "pole_id": pole_id,
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": conditions.timestamp,
                    "temperature_c": conditions.temperature_c,
                    "humidity_percent": conditions.humidity_percent,
                    "wind_speed_mph": conditions.wind_speed_mph,
                    "pressure_mb": conditions.pressure_mb,
                    "weather_description": conditions.weather_description,
                }
            )

        # Test forecast
        forecasts = weather_provider.get_forecast(lat, lon, days=3)
        if forecasts:
            logger.debug(f"  3-day forecast: {len(forecasts)} days")
            for i, forecast in enumerate(forecasts[:3]):
                logger.debug(
                    f"    Day {i+1}: {forecast.temp_min_c:.1f}°C - {forecast.temp_max_c:.1f}°C, "
                    f"{forecast.precipitation_probability:.0f}% rain, "
                    f"{forecast.wind_speed_mph:.1f} mph wind"
                )

        # Test weather alerts
        alerts = weather_provider.get_alerts(lat, lon)
        if alerts:
            logger.debug(f"  Active alerts: {len(alerts)}")
            for alert in alerts:
                logger.debug(
                    f"    {alert.title}: {alert.severity} ({alert.alert_type})"
                )
        else:
            logger.debug("  No active weather alerts")

        # Test risk assessment
        current_risks = risk_assessor.assess_current_weather_risk(lat, lon)
        forecast_risks = risk_assessor.assess_forecast_risk(lat, lon)
        combined_risks = risk_assessor.get_weather_enhanced_pole_risk(lat, lon)

        logger.debug(
            f"  Current weather risk: {current_risks['overall_weather_risk']:.3f}"
        )
        logger.debug(f"  Forecast risk: {forecast_risks['forecast_risk']:.3f}")
        logger.debug(
            f"  Combined weather risk: {combined_risks['combined_weather_risk']:.3f}"
        )

    return weather_data


def test_weather_enhanced_assessment():
    """Test integration with pole health assessment."""

    logger.debug("\n TESTING WEATHER-ENHANCED POLE ASSESSMENT:")
    logger.debug("-" * 50)

    # Load existing assessment data
    try:
        assessment_df = pd.read_csv("Output/pole_health_assessment.csv")
        logger.info(f"Loaded {len(assessment_df)} pole assessments")

        # Initialize weather provider
        weather_provider = OpenWeatherMapProvider()
        risk_assessor = WeatherRiskAssessment(weather_provider)

        # Enhance each pole assessment with weather data
        enhanced_data = []

        for _, row in assessment_df.iterrows():
            pole_id = row["pole_id"]
            lat = row["latitude"]
            lon = row["longitude"]

            # Get weather-enhanced risks
            weather_risks = risk_assessor.get_weather_enhanced_pole_risk(lat, lon)

            # Create enhanced assessment record
            enhanced_record = row.to_dict()
            enhanced_record.update(
                {
                    "current_weather_risk": weather_risks["current_weather_risk"],
                    "forecast_weather_risk": weather_risks["forecast_weather_risk"],
                    "weather_alert_risk": weather_risks["weather_alert_risk"],
                    "combined_weather_risk": weather_risks["combined_weather_risk"],
                    "wind_risk": weather_risks.get("wind_risk", 0.0),
                    "temperature_risk": weather_risks.get("temperature_risk", 0.0),
                    "precipitation_risk": weather_risks.get("precipitation_risk", 0.0),
                }
            )

            # Adjust overall health score based on weather
            weather_adjustment = (
                weather_risks["combined_weather_risk"] * 10
            )  # Max 10 point reduction
            original_score = enhanced_record["overall_health_score"]
            enhanced_record["weather_adjusted_health_score"] = max(
                0, original_score - weather_adjustment
            )

            enhanced_data.append(enhanced_record)

            logger.info(
                f"  {pole_id}: Original score {original_score:.1f} -> "
                f"Weather-adjusted {enhanced_record['weather_adjusted_health_score']:.1f} "
                f"(weather risk: {weather_risks['combined_weather_risk']:.3f})"
            )

        # Save enhanced assessment
        enhanced_df = pd.DataFrame(enhanced_data)
        enhanced_file = "Output/weather_enhanced_assessment.csv"
        enhanced_df.to_csv(enhanced_file, index=False)

        logger.debug(f"\n Weather-enhanced assessment saved to: {enhanced_file}")
        logger.debug(f"   Added {len(weather_risks)} weather risk factors")

        return enhanced_df

    except FileNotFoundError:
        logger.debug(" No existing pole assessment found. Run main assessment first.")
        return None


def create_weather_config():
    """Create weather configuration file."""

    config_content = """# Weather API Configuration
# 
# To use real weather data, sign up for a free API key at:
# https://openweathermap.org/api
# 
# Then set your API key here:
WEATHER_API_KEY=your_api_key_here

# Weather risk thresholds (can be customized)
HIGH_WIND_THRESHOLD_MPH=45
MODERATE_WIND_THRESHOLD_MPH=30
FREEZE_THRESHOLD_C=0
EXTREME_COLD_THRESHOLD_C=-10
EXTREME_HEAT_THRESHOLD_C=35

# Update frequency (minutes)
WEATHER_UPDATE_FREQUENCY=60
FORECAST_UPDATE_FREQUENCY=360

# Alert settings
ENABLE_WEATHER_ALERTS=true
ALERT_LEAD_TIME_HOURS=24
"""

    config_file = ".env.weather"
    with open(config_file, "w") as f:
        f.write(config_content)

    logger.debug(f"\n Weather configuration template created: {config_file}")
    logger.debug("   Edit this file to add your OpenWeatherMap API key for real data")


def main():
    """Main test function."""

    logger.debug(" WEATHER API INTEGRATION TEST")
    logger.debug("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.debug("=" * 60)

    try:
        # Test basic weather integration
        weather_data = test_weather_integration()

        # Test enhanced assessment
        enhanced_assessment = test_weather_enhanced_assessment()

        # Create configuration
        create_weather_config()

        logger.debug("\n" + "=" * 60)
        logger.info(" WEATHER API INTEGRATION COMPLETE")
        logger.debug("=" * 60)
        logger.debug("New capabilities added:")
        logger.debug("  • Real-time weather condition monitoring")
        logger.debug("  • 7-day weather forecast integration")
        logger.warning("  • Weather alert and warning system")
        logger.debug("  • Wind, temperature, and precipitation risk assessment")
        logger.debug("  • Weather-adjusted health scoring")
        logger.debug("\nWeather data sources:")
        logger.debug("  • OpenWeatherMap API (requires free API key)")
        logger.debug("  • Mock data generator (for testing without API key)")
        logger.debug("\nNext steps:")
        logger.debug("  1. Get free API key from openweathermap.org")
        logger.debug("  2. Add API key to .env.weather file")
        logger.debug("  3. Weather data will automatically enhance pole assessments")

    except Exception as e:
        logger.error(f" Error during weather testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
