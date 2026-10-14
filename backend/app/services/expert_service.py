"""Expert and Krishi Vigyan Kendra (KVK) Recommendation Service.

Provides verified directory lookup for ICAR-affiliated Krishi Vigyan Kendras,
state agricultural extension centers, and official helplines without fabricated information.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class ExpertService:
    def __init__(self):
        self.directory_path = Path(settings.EXPERTS_DATA_PATH)
        self.directory: List[Dict[str, Any]] = []
        self._load_directory()

    def _load_directory(self):
        """Loads verified KVK and institutional contacts."""
        if self.directory_path.exists():
            try:
                with open(self.directory_path, "r", encoding="utf-8") as f:
                    self.directory = json.load(f)
                logger.info(f"Loaded {len(self.directory)} verified expert and KVK contacts.")
            except Exception as e:
                logger.error(f"Failed to load KVK directory from {self.directory_path}: {e}")
                self.directory = []
        else:
            logger.warning(f"KVK directory file not found at {self.directory_path}")
            self.directory = []

    def lookup_experts(
        self,
        state: str,
        district: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Looks up verified agricultural support centers by State and District."""
        results = []
        state_q = state.strip().lower() if state else ""
        dist_q = district.strip().lower() if district else ""

        for entry in self.directory:
            entry_state = entry.get("state", "").lower()
            entry_dist = entry.get("district", "").lower()

            # Always include national all-India helpline (Kisan Call Centre)
            if entry_state == "all":
                results.append(entry)
                continue

            # State match
            if state_q and (state_q in entry_state or entry_state in state_q):
                if dist_q:
                    if dist_q in entry_dist or entry_dist in dist_q:
                        results.append(entry)
                    else:
                        # Keep state-level universities or institutions
                        if "university" in entry.get("type", "").lower() or "directorate" in entry.get("type", "").lower():
                            results.append(entry)
                else:
                    results.append(entry)

        # Remove duplicates while preserving order
        seen_ids = set()
        deduped = []
        for item in results:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                deduped.append(item)

        disclaimer = (
            "Contact information is curated from official ICAR and State Agricultural University directories. "
            "Please call during official government working hours (9:30 AM to 5:30 PM, Monday through Friday, except national holidays). "
            "Kisan Call Centre (1800-180-1551) operates 6:00 AM to 10:00 PM on all 7 days."
        )

        return {
            "total_found": len(deduped),
            "contacts": deduped,
            "official_directory_url": "https://kvk.icar.gov.in",
            "disclaimer": disclaimer
        }


expert_service = ExpertService()
