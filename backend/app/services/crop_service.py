"""Smart Crop Planning Recommendation Service.

Implements a transparent, rule-grounded agronomic recommendation engine
incorporating soil suitability, seasonal agro-climatic requirements, water availability,
and specific regional cautions based on ICAR guidelines.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class CropService:
    def __init__(self):
        self.rules_path = Path(settings.CROPS_DATA_PATH)
        self.crop_rules: List[Dict[str, Any]] = []
        self._load_crop_rules()

    def _load_crop_rules(self):
        """Loads agronomic rule definitions."""
        if self.rules_path.exists():
            try:
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    self.crop_rules = json.load(f)
                logger.info(f"Loaded {len(self.crop_rules)} crop planning rules.")
            except Exception as e:
                logger.error(f"Failed to load crop rules from {self.rules_path}: {e}")
                self.crop_rules = []
        else:
            logger.warning(f"Crop rules file not found at {self.rules_path}")
            self.crop_rules = []

    def recommend_crops(
        self,
        state: str,
        district: Optional[str] = None,
        season: str = "Kharif",
        soil_type: str = "Red sandy loam",
        water_availability: str = "Moderate",
        land_size_acres: Optional[float] = None,
        preferred_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluates agronomic rules to compute suitability scores and recommendations."""
        recommendations = []
        assumptions = []
        cautions = []

        # Validate inputs
        if not state:
            state = "Karnataka"
            assumptions.append("State not specified; defaulted to Karnataka.")

        if not district:
            assumptions.append("District not specified; general state-level agro-climatic conditions assumed.")

        if not land_size_acres:
            assumptions.append("Land size not provided; recommendations assume standard smallholder practices (1-2 hectares).")

        norm_season = season.strip().title()
        norm_soil = soil_type.strip().lower()
        norm_water = water_availability.strip().capitalize()

        for crop in self.crop_rules:
            # 1. Preferred category filter if specified
            if preferred_category and preferred_category.lower() not in crop.get("category", "").lower():
                continue

            score = crop.get("suitability_score_base", 0.85)

            # 2. Season matching
            season_match = False
            for s in crop.get("seasons", []):
                if norm_season.lower() in s.lower() or s.lower() in norm_season.lower():
                    season_match = True
                    break

            if not season_match:
                # Deduct heavily or skip if out of season
                score -= 0.35

            # 3. Soil suitability
            soil_compatible = False
            for soil in crop.get("soil_types", []):
                if norm_soil in soil.lower() or any(word in soil.lower() for word in norm_soil.split()):
                    soil_compatible = True
                    break

            if soil_compatible:
                score += 0.05
            else:
                score -= 0.15

            # 4. Water availability compatibility
            water_levels = crop.get("water_levels_compatible", ["Moderate"])
            if norm_water in water_levels:
                score += 0.05
            else:
                score -= 0.25

            # 5. State recommendation bonus
            states_rec = [st.lower() for st in crop.get("states_recommended", [])]
            if state.lower() in states_rec:
                score += 0.05

            score = max(0.1, min(0.99, score))

            # Include if suitability is above threshold
            if score >= 0.60:
                recommendations.append({
                    "crop_name": crop["crop_name"],
                    "variety": ", ".join(crop.get("varieties", ["Standard high-yielding varieties"])),
                    "season": norm_season,
                    "duration_days": crop.get("duration_days", "90-120 days"),
                    "suitability_score": round(score, 2),
                    "rationale": crop.get("rationale", "Agro-climatically suitable for local conditions."),
                    "water_requirement": crop.get("water_requirement", "Moderate"),
                    "soil_suitability": f"Compatible with {soil_type}",
                    "key_risks_and_cautions": crop.get("key_risks_and_cautions", [])
                })

        # Sort recommendations by suitability score descending
        recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)

        # Standard agricultural cautions
        cautions.extend([
            "Rainfall patterns can vary significantly from seasonal averages; consult the weekly IMD Agromet advisory.",
            "Soil testing at the local KVK or soil testing lab is strongly advised before purchasing fertilizers.",
            "Market prices fluctuate; check e-NAM (National Agriculture Market) mandi prices prior to finalizing crop selection."
        ])

        disclaimer = (
            "Agronomic recommendations are generated based on documented ICAR and State Agricultural Department package of practices. "
            "These suggestions do not constitute a financial or harvest guarantee. Local microclimate, pest pressures, and seed quality "
            "play critical roles in actual farm yields."
        )

        return {
            "input_summary": {
                "state": state,
                "district": district or "Not specified",
                "season": season,
                "soil_type": soil_type,
                "water_availability": water_availability,
                "land_size_acres": land_size_acres,
                "preferred_category": preferred_category or "All"
            },
            "recommendations": recommendations,
            "assumptions": assumptions,
            "cautions": cautions,
            "disclaimer": disclaimer
        }


crop_service = CropService()
