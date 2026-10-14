"""Central AI Orchestrator Service.

Implements deterministic intent classification and multi-turn query routing across:
1. Wellbeing & Crisis Safeguard (Highest Priority)
2. Government Schemes & Subsidies
3. Crop Planning & Agronomic Advisory
4. Expert & KVK Directory Lookup
5. Agricultural Knowledge Base (RAG)
6. Multilingual Response Formatting
"""

import re
from typing import Dict, Any, Optional
from backend.app.core.logging import logger
from backend.app.database.db import log_query
from backend.app.services.wellbeing_service import wellbeing_service
from backend.app.services.scheme_service import scheme_service
from backend.app.services.crop_service import crop_service
from backend.app.services.expert_service import expert_service
from backend.app.services.rag_service import rag_service
from backend.app.services.multilingual_service import multilingual_service


# Routing Keywords
SCHEME_KEYWORDS = [
    r"\bscheme(s)?\b", r"\bsubsid(y|ies)\b", r"\byojana\b", r"\bpm-?kisan\b",
    r"\bpmfby\b", r"\bloan\b", r"\bkcc\b", r"\bcredit\s+card\b", r"\binsurance\b",
    r"\bcompensation\b", r"\bಸರ್ಕಾರಿ\s+ಯೋಜನೆ\b", r"\bಸಬ್ಸಿಡಿ\b", r"\bವಿಮೆ\b",
    r"\bयोजना\b", r"\bसब्सिडी\b", r"\bबीमा\b", r"\bऋण\b"
]

CROP_PLANNING_KEYWORDS = [
    r"\bwhat\s+to\s+grow\b", r"\bwhich\s+crop\b", r"\bcrop\s+plan(ning)?\b",
    r"\bsuitable\s+crop\b", r"\bseason\b", r"\bkharif\b", r"\brabi\b", r"\bsoil\b",
    r"\bplant(ing)?\s+now\b", r"\bಯಾವ\s+ಬೆಳೆ\b", r"\bಬೆಳೆ\s+ಯೋಜನೆ\b",
    r"\bकौन\s+सी\s+फसल\b", r"\bफसल\s+चक्र\b"
]

EXPERT_KEYWORDS = [
    r"\bkvk\b", r"\bkrishi\s+vigyan\s+kendra\b", r"\bexpert\b", r"\bofficer\b",
    r"\bscientist\b", r"\buniversity\b", r"\bcontact\s+number\b", r"\bphone\b",
    r"\bcall\s+center\b", r"\bhelpline\b", r"\baddress\b", r"\bಕೃಷಿ\s+ವಿಜ್ಞಾನ\s+ಕೇಂದ್ರ\b",
    r"\bತಜ್ಞ\b", r"\bकृषि\s+विज्ञान\s+केंद्र\b", r"\bविशेषज्ञ\b"
]

DISEASE_KEYWORDS = [
    r"\bleaf\s+spot\b", r"\bblight\b", r"\byellow\s+leaves\b", r"\bfungus\b",
    r"\binsect\b", r"\bpest\b", r"\bvirus\b", r"\bwilt\b", r"\brott(ing)?\b",
    r"\bwhitefly\b", r"\barmyworm\b", r"\bరೋಗ\b", r"\bಕೀಟ\b", r"\bರೋಗಲಕ್ಷಣ\b",
    r"\bरोग\b", r"\bकीट\b", r"\bझुलसा\b"
]


class OrchestratorService:
    def __init__(self):
        self.scheme_patterns = [re.compile(p, re.IGNORECASE) for p in SCHEME_KEYWORDS]
        self.crop_patterns = [re.compile(p, re.IGNORECASE) for p in CROP_PLANNING_KEYWORDS]
        self.expert_patterns = [re.compile(p, re.IGNORECASE) for p in EXPERT_KEYWORDS]
        self.disease_patterns = [re.compile(p, re.IGNORECASE) for p in DISEASE_KEYWORDS]

    def route_and_execute(
        self,
        query: str,
        user_language: Optional[str] = None,
        location: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Routes query through safety checks, classifies intent, and dispatches to appropriate module."""
        query_clean = query.strip()
        state = (location or {}).get("state", "Karnataka")
        district = (location or {}).get("district", None)

        # 1. Detect or verify language
        detected_lang = multilingual_service.detect_language(query_clean)
        active_lang = user_language if user_language in ["en", "kn", "hi"] else detected_lang

        # 2. Priority 1: Farmer Wellbeing & Crisis Safety Check
        wellbeing_assessment = wellbeing_service.assess_wellbeing(query_clean, active_lang)
        if wellbeing_assessment["is_crisis_detected"]:
            log_query(query_clean, "wellbeing", active_lang, 1.0, wellbeing_assessment["empathetic_message"])
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "wellbeing",
                "answer": wellbeing_assessment["empathetic_message"],
                "sources": ["National Health Mission", "Tele-MANAS (14416)", "Kisan Call Centre (1800-180-1551)"],
                "structured_data": {
                    "urgency_level": wellbeing_assessment["urgency_level"],
                    "helplines": wellbeing_assessment["helplines"]
                },
                "warning": wellbeing_assessment["safety_disclaimer"]
            }

        # 3. Priority 2: Government Schemes & Loans
        if any(p.search(query_clean) for p in self.scheme_patterns):
            scheme_res = scheme_service.search_schemes(state=state, keyword=query_clean)
            answer_text = (
                f"Found {scheme_res['total_found']} relevant government schemes and subsidy programs. "
                "Key initiatives include PM-KISAN (direct income support), PMFBY (crop insurance), "
                "and Kisan Credit Card (concessional credit)."
            )
            log_query(query_clean, "schemes", active_lang, 0.95, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "schemes",
                "answer": answer_text,
                "sources": ["pmkisan.gov.in", "pmfby.gov.in", "myscheme.gov.in"],
                "structured_data": scheme_res,
                "warning": scheme_res["disclaimer"]
            }

        # 4. Priority 3: Expert & KVK Directory Lookup
        if any(p.search(query_clean) for p in self.expert_patterns):
            expert_res = expert_service.lookup_experts(state=state, district=district)
            answer_text = (
                f"Located {expert_res['total_found']} verified agricultural support contacts and KVK centers for {state}. "
                "You can also reach the all-India Kisan Call Centre directly at toll-free 1800-180-1551."
            )
            log_query(query_clean, "experts", active_lang, 0.95, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "experts",
                "answer": answer_text,
                "sources": [expert_res["official_directory_url"]],
                "structured_data": expert_res,
                "warning": expert_res["disclaimer"]
            }

        # 5. Priority 4: Crop Planning Advisory
        if any(p.search(query_clean) for p in self.crop_patterns):
            crop_res = crop_service.recommend_crops(state=state, district=district)
            top_crops = [c["crop_name"] for c in crop_res["recommendations"][:3]]
            answer_text = (
                f"Based on agro-climatic rules for {state}, suitable crops for current season include: "
                f"{', '.join(top_crops)}. Recommendation factors water requirements and soil adaptability."
            )
            log_query(query_clean, "crop_planning", active_lang, 0.90, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "crop_planning",
                "answer": answer_text,
                "sources": ["ICAR Agronomic Package of Practices", "State Agriculture Department Guidelines"],
                "structured_data": crop_res,
                "warning": crop_res["disclaimer"]
            }

        # 6. Priority 5: Crop Disease Question (Text query)
        if any(p.search(query_clean) for p in self.disease_patterns):
            # Query RAG specifically for disease guidance
            rag_res = rag_service.query(query_clean, top_k=2)
            answer_text = rag_res["grounded_answer"]
            if not rag_res["sufficient_evidence"]:
                answer_text += (
                    "\n\nTip: You can also upload a clear leaf photo on the 'Crop Disease Detection' tab "
                    "for visual deep-learning diagnosis."
                )
            log_query(query_clean, "disease_inquiry", active_lang, 0.85, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "knowledge_rag",
                "answer": answer_text,
                "sources": rag_res["sources"] or ["ICAR Plant Pathology Guidelines"],
                "structured_data": {"retrieved_chunks": rag_res["retrieved_chunks"]},
                "warning": "Visual verification by an agricultural specialist is recommended for field diagnosis."
            }

        # 7. Priority 6: General Agricultural Knowledge Base (RAG)
        rag_res = rag_service.query(query_clean, top_k=3)
        log_query(query_clean, "knowledge_rag", active_lang, 0.80, rag_res["grounded_answer"])
        return {
            "query": query_clean,
            "language": active_lang,
            "routed_module": "knowledge_rag",
            "answer": rag_res["grounded_answer"],
            "sources": rag_res["sources"] or ["ICAR Agricultural Knowledge Repository"],
            "structured_data": {"retrieved_chunks": rag_res["retrieved_chunks"]},
            "warning": "Information is grounded on indexed institutional manuals."
        }


orchestrator_service = OrchestratorService()
