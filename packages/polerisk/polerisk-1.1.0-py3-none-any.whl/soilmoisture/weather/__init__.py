"""
Weather data integration for utility pole environmental risk assessment.
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import os
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WeatherConditions:
    """Current weather conditions."""
    
    latitude: float
    longitude: float
    timestamp: datetime
    
    # Current conditions
    temperature_c: float
    humidity_percent: float
    wind_speed_mph: float
    wind_direction_deg: float
    pressure_mb: float
    
    # Precipitation
    precipitation_mm: Optional[float] = None
    rain_1h_mm: Optional[float] = None
    snow_1h_mm: Optional[float] = None
    
    # Visibility and conditions
    visibility_km: Optional[float] = None
    cloud_cover_percent: Optional[float] = None
    weather_description: Optional[str] = None
    
    # Derived conditions
    feels_like_c: Optional[float] = None
    dew_point_c: Optional[float] = None
    uv_index: Optional[float] = None


@dataclass
class WeatherForecast:
    """Weather forecast data."""
    
    latitude: float
    longitude: float
    forecast_date: datetime
    
    # Temperature forecast
    temp_max_c: float
    temp_min_c: float
    
    # Precipitation forecast
    precipitation_probability: float  # 0-100%
    
    # Wind forecast
    wind_speed_mph: float
    weather_description: str
    
    # Optional fields
    precipitation_mm: Optional[float] = None
    wind_gust_mph: Optional[float] = None
    humidity_percent: Optional[float] = None


@dataclass
class WeatherAlert:
    """Weather alert/warning information."""
    
    alert_id: str
    latitude: float
    longitude: float
    
    # Alert details
    alert_type: str  # thunderstorm, high_wind, ice_storm, etc.
    severity: str    # minor, moderate, severe, extreme
    urgency: str     # immediate, expected, future, past
    
    # Timing
    start_time: datetime
    end_time: datetime
    
    # Description
    title: str
    description: str
    
    # Impact assessment
    pole_risk_multiplier: float = 1.0  # Risk multiplier for poles


class WeatherDataProvider:
    """Weather data provider interface."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('WEATHER_API_KEY')
        if not self.api_key:
            logger.warning("No weather API key provided. Using mock data.")
    
    def get_current_conditions(self, latitude: float, longitude: float) -> Optional[WeatherConditions]:
        """Get current weather conditions."""
        raise NotImplementedError
    
    def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> List[WeatherForecast]:
        """Get weather forecast."""
        raise NotImplementedError
    
    def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        """Get weather alerts."""
        raise NotImplementedError


class OpenWeatherMapProvider(WeatherDataProvider):
    """OpenWeatherMap API provider."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
    
    def get_current_conditions(self, latitude: float, longitude: float) -> Optional[WeatherConditions]:
        """Get current weather from OpenWeatherMap."""
        
        if not self.api_key:
            return self._get_mock_current_conditions(latitude, longitude)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            conditions = WeatherConditions(
                latitude=latitude,
                longitude=longitude,
                timestamp=datetime.now(),
                temperature_c=data['main']['temp'],
                humidity_percent=data['main']['humidity'],
                wind_speed_mph=data['wind']['speed'] * 2.237,  # m/s to mph
                wind_direction_deg=data['wind'].get('deg', 0),
                pressure_mb=data['main']['pressure'],
                feels_like_c=data['main'].get('feels_like'),
                visibility_km=data.get('visibility', 0) / 1000,  # m to km
                cloud_cover_percent=data['clouds']['all'],
                weather_description=data['weather'][0]['description']
            )
            
            # Add precipitation if present
            if 'rain' in data:
                conditions.rain_1h_mm = data['rain'].get('1h', 0)
                conditions.precipitation_mm = conditions.rain_1h_mm
            
            if 'snow' in data:
                conditions.snow_1h_mm = data['snow'].get('1h', 0)
                if conditions.precipitation_mm:
                    conditions.precipitation_mm += conditions.snow_1h_mm
                else:
                    conditions.precipitation_mm = conditions.snow_1h_mm
            
            return conditions
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return self._get_mock_current_conditions(latitude, longitude)
    
    def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> List[WeatherForecast]:
        """Get weather forecast from OpenWeatherMap."""
        
        if not self.api_key:
            return self._get_mock_forecast(latitude, longitude, days)
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            
            # Group by day and take daily summaries
            daily_data = {}
            for item in data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                date_key = dt.date()
                
                if date_key not in daily_data:
                    daily_data[date_key] = []
                daily_data[date_key].append(item)
            
            # Create daily forecasts
            for date_key, day_data in list(daily_data.items())[:days]:
                temps = [item['main']['temp'] for item in day_data]
                winds = [item['wind']['speed'] * 2.237 for item in day_data]  # m/s to mph
                precip_prob = max([item['pop'] * 100 for item in day_data])  # probability of precipitation
                
                # Get midday conditions for description
                midday_item = day_data[len(day_data)//2]
                
                forecast = WeatherForecast(
                    latitude=latitude,
                    longitude=longitude,
                    forecast_date=datetime.combine(date_key, datetime.min.time()),
                    temp_max_c=max(temps),
                    temp_min_c=min(temps),
                    precipitation_probability=precip_prob,
                    wind_speed_mph=np.mean(winds),
                    wind_gust_mph=max([item['wind'].get('gust', 0) * 2.237 for item in day_data]),
                    weather_description=midday_item['weather'][0]['description'],
                    humidity_percent=np.mean([item['main']['humidity'] for item in day_data])
                )
                
                forecasts.append(forecast)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return self._get_mock_forecast(latitude, longitude, days)
    
    def get_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        """Get weather alerts from OpenWeatherMap."""
        
        if not self.api_key:
            return self._get_mock_alerts(latitude, longitude)
        
        try:
            # Note: Alerts require One Call API 3.0 subscription
            url = f"{self.onecall_url}"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'exclude': 'minutely,hourly,daily'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 401:
                # API key doesn't have One Call access
                logger.info("Weather alerts require One Call API subscription")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            if 'alerts' in data:
                for alert_data in data['alerts']:
                    alert = WeatherAlert(
                        alert_id=f"owm_{alert_data.get('sender_name', 'unknown')}_{alert_data['start']}",
                        latitude=latitude,
                        longitude=longitude,
                        alert_type=self._categorize_alert(alert_data['event']),
                        severity='moderate',  # Default, OWM doesn't provide severity levels
                        urgency='immediate' if alert_data['start'] <= datetime.now().timestamp() else 'expected',
                        start_time=datetime.fromtimestamp(alert_data['start']),
                        end_time=datetime.fromtimestamp(alert_data['end']),
                        title=alert_data['event'],
                        description=alert_data['description'],
                        pole_risk_multiplier=self._calculate_pole_risk_multiplier(alert_data['event'])
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching weather alerts: {e}")
            return []
    
    def _categorize_alert(self, event: str) -> str:
        """Categorize weather alert type."""
        event_lower = event.lower()
        
        if 'wind' in event_lower or 'gust' in event_lower:
            return 'high_wind'
        elif 'thunder' in event_lower or 'storm' in event_lower:
            return 'thunderstorm'
        elif 'ice' in event_lower or 'freezing' in event_lower:
            return 'ice_storm'
        elif 'snow' in event_lower or 'blizzard' in event_lower:
            return 'snow_storm'
        elif 'flood' in event_lower:
            return 'flooding'
        elif 'tornado' in event_lower:
            return 'tornado'
        else:
            return 'other'
    
    def _calculate_pole_risk_multiplier(self, event: str) -> float:
        """Calculate risk multiplier for poles based on weather event."""
        event_lower = event.lower()
        
        risk_multipliers = {
            'tornado': 5.0,
            'high_wind': 3.0,
            'ice_storm': 2.5,
            'thunderstorm': 2.0,
            'snow_storm': 1.5,
            'flooding': 1.3,
            'other': 1.1
        }
        
        for event_type, multiplier in risk_multipliers.items():
            if event_type in event_lower:
                return multiplier
        
        return 1.0
    
    def _get_mock_current_conditions(self, latitude: float, longitude: float) -> WeatherConditions:
        """Generate mock current conditions for testing."""
        return WeatherConditions(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_c=np.random.uniform(10, 25),
            humidity_percent=np.random.uniform(40, 80),
            wind_speed_mph=np.random.uniform(5, 20),
            wind_direction_deg=np.random.uniform(0, 360),
            pressure_mb=np.random.uniform(1000, 1030),
            precipitation_mm=np.random.uniform(0, 5) if np.random.random() > 0.7 else None,
            visibility_km=np.random.uniform(5, 15),
            cloud_cover_percent=np.random.uniform(0, 100),
            weather_description="Partly cloudy"
        )
    
    def _get_mock_forecast(self, latitude: float, longitude: float, days: int) -> List[WeatherForecast]:
        """Generate mock forecast for testing."""
        forecasts = []
        
        for i in range(days):
            forecast_date = datetime.now() + timedelta(days=i)
            
            forecast = WeatherForecast(
                latitude=latitude,
                longitude=longitude,
                forecast_date=forecast_date,
                temp_max_c=np.random.uniform(15, 30),
                temp_min_c=np.random.uniform(0, 15),
                precipitation_probability=np.random.uniform(0, 100),
                wind_speed_mph=np.random.uniform(5, 25),
                wind_gust_mph=np.random.uniform(10, 40),
                weather_description="Variable clouds",
                humidity_percent=np.random.uniform(40, 80)
            )
            
            forecasts.append(forecast)
        
        return forecasts
    
    def _get_mock_alerts(self, latitude: float, longitude: float) -> List[WeatherAlert]:
        """Generate mock alerts for testing."""
        # Return empty list for most cases, occasionally return a mock alert
        if np.random.random() > 0.8:
            alert = WeatherAlert(
                alert_id="mock_alert_001",
                latitude=latitude,
                longitude=longitude,
                alert_type="high_wind",
                severity="moderate",
                urgency="expected",
                start_time=datetime.now() + timedelta(hours=2),
                end_time=datetime.now() + timedelta(hours=8),
                title="High Wind Warning",
                description="High winds expected with gusts up to 45 mph",
                pole_risk_multiplier=2.0
            )
            return [alert]
        return []


class WeatherRiskAssessment:
    """Assess weather-related risks for utility poles."""
    
    def __init__(self, weather_provider: WeatherDataProvider):
        self.weather_provider = weather_provider
        
        # Risk thresholds
        self.wind_thresholds = {
            'high_risk': 45,     # mph
            'moderate_risk': 30,
            'low_risk': 20
        }
        
        self.temperature_thresholds = {
            'freeze_risk': 0,    # Celsius
            'extreme_cold': -10,
            'extreme_heat': 35
        }
    
    def assess_current_weather_risk(self, latitude: float, longitude: float) -> Dict[str, float]:
        """Assess current weather risks for pole location."""
        
        conditions = self.weather_provider.get_current_conditions(latitude, longitude)
        if not conditions:
            return {'weather_risk': 0.5}  # Default moderate risk
        
        risks = {}
        
        # Wind risk assessment
        wind_risk = 0.0
        if conditions.wind_speed_mph >= self.wind_thresholds['high_risk']:
            wind_risk = 1.0
        elif conditions.wind_speed_mph >= self.wind_thresholds['moderate_risk']:
            wind_risk = 0.6
        elif conditions.wind_speed_mph >= self.wind_thresholds['low_risk']:
            wind_risk = 0.3
        
        risks['wind_risk'] = wind_risk
        
        # Temperature risk assessment
        temp_risk = 0.0
        if conditions.temperature_c <= self.temperature_thresholds['extreme_cold']:
            temp_risk = 0.8
        elif conditions.temperature_c <= self.temperature_thresholds['freeze_risk']:
            temp_risk = 0.4
        elif conditions.temperature_c >= self.temperature_thresholds['extreme_heat']:
            temp_risk = 0.3
        
        risks['temperature_risk'] = temp_risk
        
        # Precipitation risk
        precip_risk = 0.0
        if conditions.precipitation_mm:
            if conditions.precipitation_mm > 20:  # Heavy rain
                precip_risk = 0.6
            elif conditions.precipitation_mm > 5:  # Moderate rain
                precip_risk = 0.3
            else:
                precip_risk = 0.1
        
        risks['precipitation_risk'] = precip_risk
        
        # Overall weather risk
        risks['overall_weather_risk'] = np.mean(list(risks.values()))
        
        return risks
    
    def assess_forecast_risk(self, latitude: float, longitude: float, days: int = 7) -> Dict[str, float]:
        """Assess weather risks from forecast data."""
        
        forecasts = self.weather_provider.get_forecast(latitude, longitude, days)
        if not forecasts:
            return {'forecast_risk': 0.5}
        
        risks = []
        severe_weather_days = 0
        
        for forecast in forecasts:
            day_risk = 0.0
            
            # Wind risk
            if forecast.wind_speed_mph >= self.wind_thresholds['high_risk']:
                day_risk += 0.4
                severe_weather_days += 1
            elif forecast.wind_speed_mph >= self.wind_thresholds['moderate_risk']:
                day_risk += 0.2
            
            # Precipitation risk
            if forecast.precipitation_probability > 80:
                day_risk += 0.3
            elif forecast.precipitation_probability > 50:
                day_risk += 0.1
            
            # Temperature extremes
            if forecast.temp_min_c <= self.temperature_thresholds['freeze_risk']:
                day_risk += 0.2
            
            risks.append(min(1.0, day_risk))
        
        return {
            'forecast_risk': np.mean(risks),
            'max_daily_risk': max(risks) if risks else 0.0,
            'severe_weather_days': severe_weather_days,
            'risk_trend': 'increasing' if len(risks) > 3 and risks[-1] > risks[0] else 'stable'
        }
    
    def get_weather_enhanced_pole_risk(self, latitude: float, longitude: float) -> Dict[str, float]:
        """Get comprehensive weather-enhanced risk assessment."""
        
        # Get current conditions risk
        current_risks = self.assess_current_weather_risk(latitude, longitude)
        
        # Get forecast risk
        forecast_risks = self.assess_forecast_risk(latitude, longitude)
        
        # Check for weather alerts
        alerts = self.weather_provider.get_alerts(latitude, longitude)
        alert_risk = 0.0
        alert_multiplier = 1.0
        
        if alerts:
            # Take highest risk alert
            alert_multipliers = [alert.pole_risk_multiplier for alert in alerts]
            alert_multiplier = max(alert_multipliers)
            alert_risk = min(1.0, (alert_multiplier - 1.0) / 4.0)  # Convert to 0-1 risk
        
        # Combine all weather risks
        combined_risk = {
            'current_weather_risk': current_risks['overall_weather_risk'],
            'forecast_weather_risk': forecast_risks['forecast_risk'],
            'weather_alert_risk': alert_risk,
            'weather_risk_multiplier': alert_multiplier,
            'combined_weather_risk': min(1.0, 
                current_risks['overall_weather_risk'] * 0.6 + 
                forecast_risks['forecast_risk'] * 0.3 + 
                alert_risk * 0.1
            )
        }
        
        # Add individual risk components
        combined_risk.update(current_risks)
        combined_risk.update(forecast_risks)
        
        return combined_risk
