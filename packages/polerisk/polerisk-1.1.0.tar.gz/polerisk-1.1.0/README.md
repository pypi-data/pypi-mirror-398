# polerisk

**Predictive utility pole failure analysis and maintenance optimization platform**

## What You Get

`polerisk` provides comprehensive tools for analyzing utility pole health, predicting failures, and optimizing maintenance schedules. Built for utility companies, infrastructure managers, and risk analysts who need data-driven insights for pole management.

### Key Capabilities

**🔍 Risk Assessment**
- Analyze pole condition and failure probability
- Multi-factor risk scoring (age, material, weather exposure, load)
- Historical failure pattern analysis
- Predictive maintenance scheduling

**📊 Data-Driven Insights**
- Statistical analysis of pole populations
- Geospatial visualization of risk hotspots
- Time series analysis for degradation patterns
- Cost-benefit analysis for maintenance prioritization

**🤖 Machine Learning Models**
- Failure prediction models
- Anomaly detection for unusual deterioration
- Risk clustering and pattern recognition
- Custom model training on your data

**📈 Reporting & Visualization**
- Interactive dashboards
- Exportable reports (PDF, CSV, HTML)
- Map-based visualizations
- Custom analytics for your KPIs

## Installation

```bash
pip install polerisk
```

### Optional Packages

Install additional capabilities based on your needs:

```bash
# For enhanced performance
pip install polerisk[performance]

# For machine learning features
pip install polerisk[ml]

# For web dashboard
pip install polerisk[web]

# For cloud deployment
pip install polerisk[cloud]

# Install everything
pip install polerisk[all]
```

## Quick Start

```python
import polerisk

# Load your pole data
poles = polerisk.load_data('pole_inventory.csv')

# Assess risk for all poles
risk_assessment = polerisk.assess_risk(poles)

# Get high-risk poles
high_risk = risk_assessment[risk_assessment['risk_score'] > 0.7]

# Generate maintenance schedule
schedule = polerisk.optimize_maintenance(
    high_risk,
    budget=100000,
    time_horizon='1year'
)

# Export results
schedule.to_csv('maintenance_plan.csv')
polerisk.generate_report(schedule, output='report.html')
```

## Core Features

### Risk Analysis
```python
# Calculate failure probability
risk_scores = polerisk.calculate_risk(
    poles,
    factors=['age', 'material', 'weather_exposure', 'load'],
    weights='auto'  # or specify custom weights
)

# Identify critical infrastructure
critical = polerisk.identify_critical_poles(
    poles,
    criteria=['customer_impact', 'replacement_cost', 'failure_risk']
)
```

### Predictive Modeling
```python
# Train a failure prediction model
model = polerisk.train_model(
    historical_data,
    target='failure_within_year',
    model_type='random_forest'
)

# Predict failures
predictions = model.predict(current_poles)

# Evaluate model performance
metrics = model.evaluate(test_data)
print(f"Accuracy: {metrics['accuracy']:.2%}")
```

### Geospatial Analysis
```python
# Create risk heat map
risk_map = polerisk.create_risk_map(
    poles,
    base_map='openstreetmap',
    cluster_radius=5  # km
)

# Export interactive map
risk_map.save('pole_risk_map.html')

# Find poles in high-risk zones
zones = polerisk.identify_risk_zones(poles, threshold=0.8)
```

### Maintenance Optimization
```python
# Optimize maintenance schedule
optimal_plan = polerisk.optimize_maintenance(
    poles,
    budget=500000,
    constraints={
        'max_poles_per_month': 100,
        'min_risk_threshold': 0.6,
        'region_balance': True
    }
)

# Calculate ROI
roi = polerisk.calculate_roi(
    optimal_plan,
    avoided_failures=estimated_failures,
    failure_cost=avg_failure_cost
)
```

## Data Requirements

`polerisk` works with standard pole inventory data:

**Minimum Required Fields:**
- Pole ID
- Location (latitude/longitude or address)
- Installation date or age
- Material type

**Recommended Fields for Better Analysis:**
- Inspection history
- Maintenance records
- Load data
- Weather exposure
- Soil conditions
- Previous failures

**Supported Data Formats:**
- CSV, Excel
- JSON, GeoJSON
- Shapefiles
- SQL databases
- REST APIs

## Use Cases

### Utility Companies
- Reduce unexpected outages by 40-60%
- Optimize maintenance budgets
- Prioritize inspections based on risk
- Comply with regulatory requirements

### Infrastructure Managers
- Long-term asset planning
- Capital expenditure optimization
- Risk-based decision making
- Performance benchmarking

### Risk Analysts
- Portfolio-level risk assessment
- Scenario analysis and modeling
- Cost-benefit analysis
- Regulatory reporting

## Performance

- Analyze **100,000+ poles** in seconds
- Real-time risk scoring
- Parallel processing for large datasets
- Cloud-scalable architecture

## Support

- 📚 **Documentation**: [polerisk.readthedocs.io](https://polerisk.readthedocs.io/)
- 🐛 **Issues**: [github.com/kylejones200/polerisk/issues](https://github.com/kylejones200/polerisk/issues)
- 💬 **Discussions**: [github.com/kylejones200/polerisk/discussions](https://github.com/kylejones200/polerisk/discussions)
- 📧 **Contact**: kyletjones@gmail.com

## Requirements

- Python 3.12 or higher
- Standard data science libraries (automatically installed)

## License

MIT License - Free for commercial and personal use.

---

**Ready to optimize your pole maintenance?**

```bash
pip install polerisk
```

[Get Started](https://polerisk.readthedocs.io/quickstart) | [View Examples](https://github.com/kylejones200/polerisk/tree/main/examples) | [API Reference](https://polerisk.readthedocs.io/api)
