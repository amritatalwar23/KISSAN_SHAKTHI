"""Short, cautious first-line answers for common farm questions.

These are general checklists, not location-specific prescriptions. The service
directs farmers to district advisories and requests crop details where timing or
input rates depend on local conditions.
"""

import re
from difflib import get_close_matches
from typing import Any, Dict, List, Optional

from backend.app.services.crop_service import crop_service


IMD_AGROMET = "https://mausam.imd.gov.in/responsive/agromet_adv_ser_state_current.php"
IPM_GUIDANCE = "https://www.icar.gov.in/en/integrated-pest-management-sustainable-approach-responsible-pest-management"
SOIL_GUIDANCE = "https://www.icar.gov.in/en/farmers-sensitized-soil-test-based-balanced-nutrient-management-icar-ccari-goa"

ADVISORIES = [
    {
        "module": "weather_advisory",
        "patterns": [r"\bflood(s|ing)?\b", r"\bwaterlog(ging|ged)?\b", r"\bdrought\b", r"\bdry spell\b", r"\bheat ?wave\b", r"\bhot weather\b", r"\bfrost\b", r"\bcold wave\b", r"\bhail(storm)?\b", r"\bheavy rain(fall)?\b"],
        "answer": (
            "Weather actions depend on your district, crop, and growth stage. Check the latest IMD district/block "
            "agromet advisory before irrigating, spraying, fertilizing, or harvesting.\n\n"
            "For heavy rain or flood risk, keep field drains/outlets clear and avoid adding irrigation; after the event, "
            "remove standing water when safe and inspect crops for lodging and disease. During dry spells, conserve "
            "soil moisture with locally suitable mulch and prioritize water for sensitive crop stages. For heat, frost, "
            "or hail, follow the specific local warning and crop advisory.\n\n"
            "Tell me your district, crop, and crop stage and I can help interpret the general steps. "
            "[Current IMD agromet advisories](" + IMD_AGROMET + ")."
        ),
    },
    {
        "module": "irrigation_advisory",
        "patterns": [r"\birrigat(e|ion|ing)\b", r"\bdrip\b", r"\bwater my (crop|plant)", r"\bhow often.*water", r"\bwater requirement\b"],
        "answer": (
            "There isn't one safe watering schedule for every plant. Water when the soil around the active roots is starting "
            "to dry, rather than automatically watering every day. For potted plants, check the top few centimetres; for field "
            "crops, check moisture in the root zone. Water thoroughly, then let excess drain; avoid keeping roots waterlogged. "
            "Hot weather and sandy soil usually mean checking more often; rain and heavier soils mean checking less often. "
            "Tell me the plant/crop, whether it's in a pot or field, and your soil type and I can suggest a more suitable interval.\n\n"
            "[IMD district agromet advisories](" + IMD_AGROMET + ")."
        ),
    },
    {
        "module": "soil_nutrient_advisory",
        "patterns": [r"\bfertilizer(s)?\b", r"\bfertiliser(s)?\b", r"\bmanure\b", r"\bnpk\b", r"\bsoil test\b", r"\bsoil health\b", r"\bnutrient(s)?\b"],
        "answer": (
            "For fertilizer decisions, start with a recent soil test and follow its crop-specific recommendation; a blanket "
            "dose can waste money or worsen nutrient imbalance. Use well-decomposed organic matter where appropriate, "
            "and apply inputs at the recommended crop stage and rate. Avoid applying fertilizer immediately before heavy rain. "
            "Share your crop, district, soil-test values, and crop stage and I can help explain the report.\n\n"
            "[ICAR guidance on soil-test-based nutrient management](" + SOIL_GUIDANCE + ")."
        ),
    },
    {
        "module": "integrated_pest_management",
        "patterns": [r"\bprevent pests?\b", r"\bpest control\b", r"\b(control|manage)\b.{0,30}\bpests?\b", r"\binsect attack\b", r"\bwhat pesticide\b", r"\bwhich pesticide\b", r"\bwhen should i spray\b"],
        "answer": (
            "Use integrated pest management: inspect the crop regularly, identify the pest before treating, remove or manage "
            "affected plant material where appropriate, and use locally recommended cultural, mechanical, or biological controls first. "
            "Use a pesticide only when an agricultural specialist or current crop advisory recommends it; follow the product label, "
            "protective equipment requirements, and pre-harvest interval. Don't mix products or guess a dose. Tell me the crop, "
            "district, pest/symptoms, and crop stage (a clear photo helps).\n\n"
            "[ICAR integrated pest-management guidance](" + IPM_GUIDANCE + ")."
        ),
    },
    {
        "module": "harvest_storage_advisory",
        "patterns": [r"\bharvest(ing)?\b", r"\bstor(e|age|ing)\b.{0,30}\b(crop|grain|produce|seed)s?\b", r"\bpost.?harvest\b"],
        "answer": (
            "Harvest timing and storage needs differ by crop. Harvest at the locally recommended maturity, avoid harvesting "
            "wet produce when it can safely be delayed, and protect harvested produce from rain and ground moisture. Dry grain "
            "to the crop-specific safe moisture level before storage; use a clean, dry, pest-checked store and inspect it regularly. "
            "Tell me the crop and whether it is for food, seed, or sale so I can narrow the guidance.\n\n"
            "[IMD agromet advisories](" + IMD_AGROMET + ")."
        ),
    },
    {
        "module": "seed_sowing_advisory",
        "patterns": [r"\bseed(s)?\b", r"\bsow(ing)?\b", r"\btransplant(ing)?\b", r"\bplant(ing)? season\b"],
        "answer": (
            "Choose a locally recommended variety and sowing window for your district and season; use certified seed from a "
            "reliable source and follow the package/extension recommendation for seed rate and treatment. Check the short-range "
            "weather and make sure the field has suitable moisture and drainage before sowing or transplanting. Tell me your "
            "district, crop, season, and whether the field is irrigated or rain-fed.\n\n"
            "[Current IMD agromet advisories](" + IMD_AGROMET + ")."
        ),
    },
    {
        "module": "farm_productivity_advisory",
        "patterns": [r"\bincrease (my )?(crop )?yield\b", r"\bimprove (my )?(crop )?yield\b", r"\bmore yield\b", r"\bimprove productivity\b"],
        "answer": (
            "There isn't one input that reliably increases yield in every field. Start with a soil test and a locally "
            "recommended variety and sowing window; use balanced nutrients, timely water with good drainage, and regular "
            "weed/pest scouting. Keep basic notes on seed, inputs, rainfall, and harvest so you can compare results. Avoid "
            "extra fertilizer or pesticide without a diagnosed need. Tell me your crop, district, season, and current growth "
            "stage and I can make the next steps more specific.\n\n"
            "[ICAR soil-test-based nutrient guidance](" + SOIL_GUIDANCE + ") and "
            "[IMD crop-weather advisories](" + IMD_AGROMET + ")."
        ),
    },
]


class FarmAdvisoryService:
    SPELLING_VOCABULARY = {
        "water", "watering", "irrigate", "irrigation", "fertilizer", "fertiliser", "manure",
        "pesticide", "pest", "crop", "cyclone", "flood", "drought", "harvest", "storage",
        "sowing", "seed", "soil", "yield", "disease", "tomato", "maize", "rice", "banana",
    }

    def __init__(self):
        self.crop_aliases = {
            "tomato": ("tomatoes",), "potato": ("potatoes",), "maize": ("corn",),
            "paddy": ("rice",), "bengal gram": ("chickpea", "chana"),
            "red gram": ("pigeonpea", "tur"), "ragi": ("finger millet",),
        }
        self.crop_names = [crop.get("crop_name", "") for crop in crop_service.crop_rules]
        self.advisories = [
            (entry, [re.compile(pattern, re.IGNORECASE) for pattern in entry["patterns"]])
            for entry in ADVISORIES
        ]

    def _normalize_spelling(self, query: str) -> str:
        corrected_words = []
        for word in re.findall(r"[A-Za-z]+|[^A-Za-z]+", query):
            if word.isalpha() and len(word) >= 4 and word.lower() not in self.SPELLING_VOCABULARY:
                match = get_close_matches(word.lower(), self.SPELLING_VOCABULARY, n=1, cutoff=0.82)
                corrected_words.append(match[0] if match else word)
            else:
                corrected_words.append(word)
        return "".join(corrected_words)

    def _find_crop(self, text: str) -> Optional[str]:
        normalized = text.lower()
        matches = []
        for canonical in sorted(self.crop_names, key=len, reverse=True):
            base_name = canonical.lower().split(" (")[0]
            names = [canonical.lower(), base_name, *self.crop_aliases.get(base_name, ())]
            for name in names:
                for match in re.finditer(rf"\b{re.escape(name)}(s)?\b", normalized):
                    matches.append((match.start(), len(name), canonical))
        if not matches:
            return None
        return max(matches, key=lambda item: (item[0], item[1]))[2]

    def answer(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        """Return the first matching general checklist; None means route elsewhere."""
        history_text = " ".join(
            str(turn.get("content", "")) for turn in (conversation_history or [])[-8:]
            if turn.get("role") == "user"
        )
        normalized_query = self._normalize_spelling(query)
        normalized_context = self._normalize_spelling(f"{history_text} {query}")
        matched_entry = None
        follow_up = bool(re.search(
            r"\b(what about|how about|how often|and for|then|also|it|that|those|same|"
            r"i (grow|have|plant|am growing)|my (crop|plant|plants)|for (the|my|this))\b",
            normalized_query,
            re.IGNORECASE,
        )) or (len(normalized_query.split()) <= 2 and self._find_crop(normalized_query) is not None)
        for entry, patterns in self.advisories:
            if any(pattern.search(normalized_query) for pattern in patterns):
                matched_entry = entry
                break
        if matched_entry is None and follow_up:
            for entry, patterns in self.advisories:
                if any(pattern.search(normalized_context) for pattern in patterns):
                    matched_entry = entry
                    break
        if matched_entry is None:
            return None

        answer = matched_entry["answer"]
        source_links = re.findall(r"\]\((https?://[^)]+)\)", answer)
        answer = re.sub(r"\n\n\[.*$", "", answer, flags=re.DOTALL).strip()
        # Explicit crop in the latest message always overrides an older crop
        # mentioned earlier in the conversation.
        crop = self._find_crop(normalized_query) or self._find_crop(normalized_context)
        if crop and matched_entry["module"] == "irrigation_advisory":
            answer = (
                f"For {crop}, water based on moisture around its active roots, not a fixed daily schedule. "
                "Check the root zone and recent rain; water when it is starting to dry, and avoid waterlogging. "
                "Hot weather and sandy soil usually mean checking more often. Share your district and whether it is "
                "in a pot or field if you want me to narrow the interval."
            )
        elif crop and matched_entry["module"] == "harvest_storage_advisory" and crop.lower().startswith("potato"):
            answer = (
                "For potatoes, harvest when most tops have turned yellow-brown and the tuber skin no longer rubs off "
                "easily. This is often around 75-120 days after planting, depending on variety and conditions, so use "
                "the crop signs rather than the calendar alone. After cutting the tops, wait about 8-15 days for the "
                "skin to set before digging, following local advice. Harvest in dry weather and handle tubers gently; "
                "keep them shaded after lifting. If you share the variety and planting date, I can help estimate the window."
            )
            source_links = [
                "https://www.nhb.gov.in/pdf/vegetable/potato/pot004.pdf",
                "https://agmarknet.gov.in/Others/profile-potato.pdf",
            ]
        elif crop and matched_entry["module"] == "harvest_storage_advisory" and crop.lower().startswith("tomato"):
            answer = (
                "For tomatoes, first picking often starts about 60-75 days after transplanting, but variety and weather "
                "change the timing. Pick at mature-green for long-distance transport, pink for nearby markets, or fully "
                "red-ripe for immediate use or processing. Avoid picking immature dark-green fruit. If you share the "
                "variety and transplanting date, I can estimate your first-picking window."
            )
            source_links = [
                "https://www.icar.gov.in/sites/default/files/2026-05/Indian%20Horticulture%2C%20May-June%202026%20Low%20new.pdf",
                "https://nhb.gov.in/bulletin_files/vegetable/tomato/tom004.pdf",
            ]
        elif crop:
            answer = answer.replace("your crop, district", f"{crop}, district")
            answer = answer.replace("the crop, district", f"{crop}, district")
            answer = answer.replace("your district, crop, and crop stage", f"your district and {crop}'s crop stage")
            if matched_entry["module"] == "harvest_storage_advisory":
                answer = answer.replace(
                    "Tell me the crop and whether it is for food, seed, or sale so I can narrow the guidance.",
                    f"For a more precise harvest window for {crop}, share the variety and planting date."
                )
        return {"routed_module": matched_entry["module"], "answer": answer, "sources": source_links}


farm_advisory_service = FarmAdvisoryService()
