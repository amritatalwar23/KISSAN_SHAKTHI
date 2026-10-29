"""Government Schemes and Subsidies Assistance Service.

Provides verified search, eligibility filtering, and official portal linking
for Indian Central and State agricultural assistance programs.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class SchemeService:
    def __init__(self):
        self.data_path = Path(settings.SCHEMES_DATA_PATH)
        self.schemes: List[Dict[str, Any]] = []
        self._load_schemes()

    def _load_schemes(self):
        """Loads verified scheme dataset."""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.schemes = json.load(f)
                logger.info(f"Loaded {len(self.schemes)} agricultural schemes.")
            except Exception as e:
                logger.error(f"Failed to load schemes from {self.data_path}: {e}")
                self.schemes = []
        else:
            logger.warning(f"Schemes data file not found at {self.data_path}")
            self.schemes = []

    def search_schemes(
        self,
        state: Optional[str] = None,
        category: Optional[str] = None,
        crop: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """Filters schemes based on location, farmer category, crop type, or keywords."""
        results = []
        state_query = state.strip().lower() if state else None
        category_query = category.strip().lower() if category else None
        crop_query = crop.strip().lower() if crop else None
        keyword_query = keyword.strip().lower() if keyword else None
        # Farmer questions are full sentences. Match their meaningful terms to
        # scheme records instead of requiring the entire sentence as a substring.
        query_terms = set(re.findall(r"[a-z0-9]+", keyword_query or ""))
        query_terms -= {"the", "and", "for", "from", "about", "what", "which", "how", "can", "tell", "me", "is", "are", "my", "i", "am", "do", "does", "farmer", "farmers", "scheme", "schemes", "please", "benefits", "benefit"}
        aliases = {
            "pmkisan": {"pm", "kisan", "pmkisan"}, "pm-kisan": {"pm", "kisan", "pmkisan"},
            "pmfby": {"pmfby", "insurance", "crop"}, "loan": {"credit", "kcc"},
            "subsidy": {"subsidy", "support"}, "insurance": {"insurance", "pmfby"},
        }

        for item in self.schemes:
            # 1. State filter: match state specifically or All-India central schemes
            item_state = item.get("state", "").lower()
            if state_query and item_state != "all":
                if state_query not in item_state:
                    continue

            # 2. Crop filter
            if crop_query:
                text_blob = f"{item.get('name', '')} {item.get('benefits', '')} {item.get('target_beneficiaries', '')}".lower()
                # If scheme is general to all crops or specifically mentions crop
                if "all" not in text_blob and crop_query not in text_blob:
                    # Specific exclusion for specialized crops like millets
                    if "millet" in text_blob and crop_query not in ["millet", "ragi", "jowar", "bajra"]:
                        continue

            # 3. Keyword search
            if query_terms:
                combined_text = (
                    f"{item.get('name', '')} {item.get('benefits', '')} "
                    f"{' '.join(item.get('eligibility_criteria', []))} "
                    f"{item.get('target_beneficiaries', '')}"
                ).lower()
                record_terms = set(re.findall(r"[a-z0-9]+", combined_text))
                expanded_terms = set(query_terms)
                for term in query_terms:
                    expanded_terms.update(aliases.get(term, set()))
                matched = expanded_terms & record_terms
                # Keep a record when it matches at least one specific user term.
                if not matched:
                    continue

                item = dict(item)
                item["_match_score"] = len(matched)
            results.append(item)

        if query_terms:
            results.sort(key=lambda item: item.get("_match_score", 0), reverse=True)
            for item in results:
                item.pop("_match_score", None)

        disclaimer = (
            "Disclaimer: Scheme information is compiled from official government portals and gazettes. "
            "Eligibility criteria, budget allocations, and deadlines are subject to official verification "
            "at the local Taluk/District Agriculture Office or respective official portal."
        )

        return {
            "total_found": len(results),
            "schemes": results,
            "disclaimer": disclaimer
        }


scheme_service = SchemeService()
