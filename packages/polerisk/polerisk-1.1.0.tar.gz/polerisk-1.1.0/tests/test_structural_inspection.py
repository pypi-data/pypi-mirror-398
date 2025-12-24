#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the enhanced structural inspection capabilities.
"""

import pandas as pd
from datetime import datetime, timedelta
import random
import os
import sys
import logging

# Add the project root to Python path
sys.path.append("/Users/k.jones/Documents/moisture")

from soilmoisture.pole_health.enhanced_models import (
    StructuralInspection,
    InspectionType,
    PoleCondition,
    EnhancedPoleInfo,
)
from soilmoisture.pole_health.structural_assessment import (
    StructuralConditionAnalyzer,
    EnhancedPoleHealthAssessment,
)

logger = logging.getLogger(__name__)


def create_sample_structural_inspections():
    """Create sample structural inspection data."""

    inspections = []
    pole_ids = ["P001", "P002", "P003"]

    for pole_id in pole_ids:
        # Create inspection for each pole
        inspection = StructuralInspection(
            inspection_id=f"INS_{pole_id}_{datetime.now().strftime('%Y%m%d')}",
            pole_id=pole_id,
            inspection_date=datetime.now() - timedelta(days=random.randint(1, 90)),
            inspector_id="INSP001",
            inspection_type=InspectionType.DETAILED,
            overall_condition=random.choice(list(PoleCondition)),
            visible_damage=random.choice([True, False]),
            damage_description=(
                "Minor surface weathering" if random.random() > 0.5 else None
            ),
            # Material-specific data based on pole type
            wood_decay_depth=random.uniform(0.5, 2.5) if pole_id == "P001" else None,
            wood_circumferential_loss=(
                random.uniform(5, 35) if pole_id == "P001" else None
            ),
            concrete_cracking=(
                random.choice([True, False]) if pole_id == "P002" else None
            ),
            concrete_spalling=(
                random.choice([True, False]) if pole_id == "P002" else None
            ),
            steel_corrosion_level=random.randint(1, 4) if pole_id == "P003" else None,
            coating_condition=(
                random.choice(["excellent", "good", "fair", "poor"])
                if pole_id == "P003"
                else None
            ),
            # Geometry measurements
            ground_line_circumference=random.uniform(35, 55),
            lean_angle=random.uniform(-2, 4),
            twist_angle=random.uniform(-1, 2),
            # Strength assessment
            estimated_remaining_strength=random.uniform(60, 95),
            # Documentation
            photo_paths=[
                f"photos/{pole_id}_inspection_1.jpg",
                f"photos/{pole_id}_inspection_2.jpg",
            ],
            notes=f"Routine inspection of pole {pole_id}. Overall condition appears stable.",
            confidence_level=random.uniform(0.8, 1.0),
            recommended_action=(
                "Continue monitoring"
                if random.random() > 0.3
                else "Schedule follow-up inspection"
            ),
            next_inspection_date=datetime.now()
            + timedelta(days=random.randint(180, 720)),
        )

        inspections.append(inspection)

    return inspections


def test_structural_analysis():
    """Test the structural condition analysis."""

    logger.debug(" TESTING STRUCTURAL INSPECTION INTEGRATION")
    logger.debug("=" * 50)

    # Create sample inspections
    inspections = create_sample_structural_inspections()

    # Initialize analyzer
    analyzer = StructuralConditionAnalyzer()

    logger.debug("\n STRUCTURAL INSPECTION ANALYSIS:")
    logger.debug("-" * 40)

    for inspection in inspections:
        logger.debug(f"\nPole ID: {inspection.pole_id}")
        logger.debug(
            f"Inspection Date: {inspection.inspection_date.strftime('%Y-%m-%d')}"
        )
        logger.debug(f"Overall Condition: {inspection.overall_condition.value}")
        logger.debug(f"Inspector Assessment: {inspection.overall_condition.value}")

        # Determine pole type based on ID (from our sample data)
        pole_type_map = {"P001": "wood", "P002": "concrete", "P003": "steel"}
        pole_type = pole_type_map.get(inspection.pole_id, "wood")

        # Calculate condition score
        condition_score = analyzer.calculate_overall_condition_score(
            inspection, pole_type
        )
        logger.debug(f"Calculated Condition Score: {condition_score:.1f}/100")

        # Get inspection frequency recommendation
        pole_age = (
            15
            if inspection.pole_id == "P001"
            else (20 if inspection.pole_id == "P002" else 10)
        )
        frequency = analyzer.determine_inspection_frequency(
            condition_score, pole_age, pole_type
        )
        logger.debug(f"Recommended Inspection Frequency: {frequency} months")

        # Get maintenance recommendations
        recommendations = analyzer.generate_recommendations(
            inspection, condition_score, pole_type
        )
        logger.debug("Maintenance Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            logger.debug(f"  {i}. {rec}")

        # Material-specific assessments
        if pole_type == "wood":
            wood_risks = analyzer.assess_wood_condition(inspection)
            if wood_risks:
                logger.debug(f"Wood-specific Risks: {wood_risks}")
        elif pole_type == "concrete":
            concrete_risks = analyzer.assess_concrete_condition(inspection)
            if concrete_risks:
                logger.debug(f"Concrete-specific Risks: {concrete_risks}")
        elif pole_type == "steel":
            steel_risks = analyzer.assess_steel_condition(inspection)
            if steel_risks:
                logger.debug(f"Steel-specific Risks: {steel_risks}")

        # Geometry assessment
        geometry_risks = analyzer.assess_structural_geometry(inspection)
        if geometry_risks:
            logger.debug(f"Geometry Risks: {geometry_risks}")

    return inspections


def save_inspection_data(inspections):
    """Save inspection data to CSV for integration testing."""

    inspection_data = []
    for insp in inspections:
        data = {
            "inspection_id": insp.inspection_id,
            "pole_id": insp.pole_id,
            "inspection_date": insp.inspection_date.strftime("%Y-%m-%d"),
            "inspector_id": insp.inspector_id,
            "inspection_type": insp.inspection_type.value,
            "overall_condition": insp.overall_condition.value,
            "visible_damage": insp.visible_damage,
            "damage_description": insp.damage_description,
            "wood_decay_depth": insp.wood_decay_depth,
            "wood_circumferential_loss": insp.wood_circumferential_loss,
            "concrete_cracking": insp.concrete_cracking,
            "concrete_spalling": insp.concrete_spalling,
            "steel_corrosion_level": insp.steel_corrosion_level,
            "coating_condition": insp.coating_condition,
            "ground_line_circumference": insp.ground_line_circumference,
            "lean_angle": insp.lean_angle,
            "twist_angle": insp.twist_angle,
            "estimated_remaining_strength": insp.estimated_remaining_strength,
            "confidence_level": insp.confidence_level,
            "recommended_action": insp.recommended_action,
            "notes": insp.notes,
        }
        inspection_data.append(data)

    df = pd.DataFrame(inspection_data)

    # Ensure Input directory exists
    os.makedirs("Input", exist_ok=True)

    # Save to CSV
    csv_file = "Input/sample_structural_inspections.csv"
    df.to_csv(csv_file, index=False)

    logger.debug(f"\n Structural inspection data saved to: {csv_file}")
    logger.debug(f"   Records: {len(inspection_data)}")
    logger.debug(f"   Columns: {len(df.columns)}")

    return csv_file


def main():
    """Main test function."""

    logger.debug(" STRUCTURAL INSPECTION SYSTEM TEST")
    logger.debug("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.debug("=" * 60)

    try:
        # Test structural analysis
        inspections = test_structural_analysis()

        # Save sample data
        csv_file = save_inspection_data(inspections)

        logger.debug("\n" + "=" * 60)
        logger.info(" STRUCTURAL INSPECTION INTEGRATION COMPLETE")
        logger.debug("=" * 60)
        logger.debug("New capabilities added:")
        logger.debug("  • Physical condition assessment")
        logger.debug("  • Material-specific risk analysis")
        logger.debug("  • Geometry and alignment checks")
        logger.debug("  • Automated maintenance recommendations")
        logger.debug("  • Inspection frequency optimization")
        logger.debug(f"\nSample data created: {csv_file}")
        logger.debug("\nNext: Integrate with main assessment system")

    except Exception as e:
        logger.error(f" Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
