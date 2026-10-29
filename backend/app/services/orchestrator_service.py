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
from datetime import date
from typing import Dict, Any, Optional
from backend.app.core.logging import logger
from backend.app.database.db import log_query
from backend.app.services.wellbeing_service import wellbeing_service
from backend.app.services.scheme_service import scheme_service
from backend.app.services.crop_service import crop_service
from backend.app.services.expert_service import expert_service
from backend.app.services.rag_service import rag_service
from backend.app.services.multilingual_service import multilingual_service
from backend.app.services.farm_advisory_service import farm_advisory_service
from backend.app.services.generative_assistant_service import generative_assistant_service


# Routing Keywords
SCHEME_KEYWORDS = [
    r"\bscheme(s)?\b", r"\bsubsid(y|ies)\b", r"\byojana\b", r"\bpm-?kisan\b",
    r"\bpmfby\b", r"\bloan\b", r"\bkcc\b", r"\bcredit\s+card\b", r"\binsurance\b",
    r"\bcompensation\b", r"\bಸರ್ಕಾರಿ\s+ಯೋಜನೆ\b", r"\bಸಬ್ಸಿಡಿ\b", r"\bವಿಮೆ\b",
    r"\bयोजना\b", r"\bसब्सिडी\b", r"\bबीमा\b", r"\bऋण\b"
]

CROP_PLANNING_KEYWORDS = [
    r"\bwhat\s+to\s+grow\b", r"\bwhich\s+crop\b", r"\bcrop\s+plan(ning)?\b",
    r"\bsuitable\s+crop\b", r"\bwhat\s+to\s+plant\b", r"\bkharif\b", r"\brabi\b", r"\bzaid\b",
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
    r"\bvirus\b", r"\bwilt\b", r"\brott(ing)?\b",
    r"\bwhitefly\b", r"\barmyworm\b", r"\bరೋಗ\b", r"\bಕೀಟ\b", r"\bರೋಗಲಕ್ಷಣ\b",
    r"\bरोग\b", r"\bकीट\b", r"\bझुलसा\b"
]

CYCLONE_KEYWORDS = [
    r"\bcyclone(s)?\b", r"\bcyclonic\b", r"\bstorm\s+surge\b", r"\btyphoon(s)?\b",
    r"\bhurricane(s)?\b", r"\bstrong\s+wind(s)?\b", r"\bhigh\s+wind(s)?\b"
]


class OrchestratorService:
    def __init__(self):
        self.scheme_patterns = [re.compile(p, re.IGNORECASE) for p in SCHEME_KEYWORDS]
        self.crop_patterns = [re.compile(p, re.IGNORECASE) for p in CROP_PLANNING_KEYWORDS]
        self.expert_patterns = [re.compile(p, re.IGNORECASE) for p in EXPERT_KEYWORDS]
        self.disease_patterns = [re.compile(p, re.IGNORECASE) for p in DISEASE_KEYWORDS]
        self.cyclone_patterns = [re.compile(p, re.IGNORECASE) for p in CYCLONE_KEYWORDS]

    def route_and_execute(
        self,
        query: str,
        user_language: Optional[str] = None,
        location: Optional[Dict[str, str]] = None,
        conversation_history: Optional[list] = None
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

        # Cyclone readiness is actionable even though the local RAG corpus has
        # only a small number of crop disease and agronomy bulletins.
        if any(p.search(query_clean) for p in self.cyclone_patterns):
            answer_text = (
                "You can't prevent a cyclone, but you can reduce crop losses. **Follow IMD alerts and local "
                "Agriculture Department/KVK instructions first; protect people and livestock before attempting field work.**\n\n"
                "**Before strong winds and rain:**\n"
                "- Harvest mature crops and move harvested produce, seed, fertilizer, and tools to a raised, secure place. "
                "Do this only while it is safe.\n"
                "- Clear field drains and outlets so water can leave; check bunds and drainage channels.\n"
                "- Stake or prop vegetables, young fruit plants, banana, and sugarcane where practical; earth up the base of standing crops.\n"
                "- Secure nursery covers, irrigation equipment, and loose materials. Avoid spraying pesticides or applying fertilizer during the storm.\n\n"
                "**During the cyclone:** stay indoors or in a safe shelter. Do not work in fields, go near floodwater, or touch fallen power lines.\n\n"
                "**After it passes:** wait for the all-clear, drain standing water promptly, carefully prop lodged plants, and photograph crop losses "
                "for records/insurance. Contact your local KVK for crop-specific recovery advice. These steps reduce risk but cannot prevent all damage."
            )
            log_query(query_clean, "cyclone_preparedness", active_lang, 0.95, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "cyclone_preparedness",
                "answer": answer_text,
                "sources": [
                    "https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf",
                    "https://icar.gov.in/sites/default/files/2022-06/Post-Fani-advisory-for-horticultural-crops.pdf"
                ],
                "structured_data": {"preparedness_guidance": True},
                "warning": "Use current IMD alerts and district-specific advisories; timing and safe actions depend on the local forecast."
            }

        # 3. Priority 2: Government Schemes & Loans
        if any(p.search(query_clean) for p in self.scheme_patterns):
            scheme_res = scheme_service.search_schemes(state=state, keyword=query_clean)
            if scheme_res["schemes"]:
                answer_text = f"I found {scheme_res['total_found']} matching scheme(s) for {state}:\n\n"
                for item in scheme_res["schemes"][:5]:
                    criteria = item.get("eligibility_criteria", [])
                    eligibility = "; ".join(criteria[:2]) if criteria else item.get("target_beneficiaries", "Check the official portal for eligibility.")
                    answer_text += (
                        f"**{item.get('name', 'Government scheme')}**\n"
                        f"{item.get('benefits', 'See the official portal for benefit details.')}\n"
                        f"Eligibility: {eligibility}\n"
                        "\n"
                    )
                if scheme_res["total_found"] > 5:
                    answer_text += f"Showing 5 of {scheme_res['total_found']} matches. Use the Government Schemes page to filter further."
            else:
                answer_text = (
                    f"I couldn't find a matching scheme in the local directory for {state}. "
                    "Tell me the scheme name, crop, or whether you need income support, crop insurance, credit, or irrigation help. "
                    "You can also check the official MyScheme portal."
                )
            log_query(query_clean, "schemes", active_lang, 0.95, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "schemes",
                "answer": answer_text,
                "sources": sorted({item.get("official_link", "") for item in scheme_res["schemes"] if item.get("official_link")}),
                "structured_data": scheme_res,
                "warning": scheme_res["disclaimer"]
            }

        # 4. Priority 3: Expert & KVK Directory Lookup
        if any(p.search(query_clean) for p in self.expert_patterns):
            expert_res = expert_service.lookup_experts(state=state, district=district)
            answer_text = f"I found {expert_res['total_found']} support contact(s) for {district + ', ' if district else ''}{state}:\n\n"
            for contact in expert_res["contacts"][:5]:
                answer_text += f"**{contact['name']}**\n{contact.get('address', '')}\n"
                if contact.get("phone"):
                    answer_text += f"Phone: {contact['phone']}\n"
                if contact.get("email"):
                    answer_text += f"Email: {contact['email']}\n"
                answer_text += "\n"
            if not expert_res["contacts"]:
                answer_text += "No local contact matched the selected location. Specify your district or use the national Kisan Call Centre: 1800-180-1551."
            log_query(query_clean, "experts", active_lang, 0.95, answer_text)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "experts",
                "answer": answer_text,
                "sources": sorted({contact.get("official_link", expert_res["official_directory_url"]) for contact in expert_res["contacts"]}),
                "structured_data": expert_res,
                "warning": expert_res["disclaimer"]
            }

        # 5. Priority 4: Crop Planning Advisory
        if any(p.search(query_clean) for p in self.crop_patterns):
            q_lower = query_clean.lower()
            season = next((s for s in ("Kharif", "Rabi", "Zaid") if re.search(rf"\b{s.lower()}\b", q_lower)), None)
            if not season and re.search(r"\b(now|current season|right now)\b", q_lower):
                # Broad India cropping calendar; local sowing windows vary by district.
                season = {"Kharif": (6, 10), "Rabi": (10, 3), "Zaid": (3, 6)}
                month = date.today().month
                season = next((name for name, (start, end) in season.items()
                               if (start <= month < end if start < end else month >= start or month < end)), "Rabi")
            season = season or "Kharif"
            soil = next((value for value in ("black", "red", "alluvial", "clay", "sandy", "loamy") if value in q_lower), "Red sandy loam")
            water = next((value for value in ("Low", "Moderate", "High") if re.search(rf"\b{value.lower()}\b", q_lower)), "Moderate")
            crop_res = crop_service.recommend_crops(state=state, district=district, season=season, soil_type=soil, water_availability=water)
            top_crops = [c["crop_name"] for c in crop_res["recommendations"][:3]]
            answer_text = (f"For {state} ({district or 'district not specified'}), the rule based shortlist for {season} "
                           f"with {soil} soil and {water.lower()} water availability is: "
                           f"{', '.join(top_crops)}." if top_crops else
                           f"I couldn't identify a suitable crop from the current rules for {state} under {season}, {soil} soil, and {water.lower()} water conditions.")
            if crop_res["recommendations"]:
                answer_text += "\n\n" + "\n".join(
                    f"- **{c['crop_name']}** ({c['suitability_score']:.0%} rule score): {c['rationale']}"
                    for c in crop_res["recommendations"][:3]
                )
            answer_text += "\n\nThese are preliminary options, not a yield guarantee. Share your district, soil test, water access, and sowing month for a more specific shortlist."
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
            if not rag_res["sufficient_evidence"]:
                general_advice = farm_advisory_service.answer(query_clean, conversation_history)
                if general_advice:
                    log_query(query_clean, general_advice["routed_module"], active_lang, 0.65, general_advice["answer"])
                    return {
                        "query": query_clean,
                        "language": active_lang,
                        **general_advice,
                        "structured_data": {},
                        "warning": "This is general preventive guidance. For treatment, identify the pest or disease and follow crop-specific local recommendations."
                    }
            answer_text = rag_res.get("chat_answer", rag_res["grounded_answer"])
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
                "sources": rag_res["sources"],
                "structured_data": {"retrieved_chunks": rag_res["retrieved_chunks"], "full_advisory": rag_res["grounded_answer"]},
                "warning": ("Visual verification by an agricultural specialist is recommended for field diagnosis."
                            if rag_res["sufficient_evidence"] else "The local advisory index did not contain enough evidence to recommend a treatment.")
            }

        general_advice = farm_advisory_service.answer(query_clean, conversation_history)
        if general_advice:
            model_answer = generative_assistant_service.answer(
                question=query_clean,
                language=active_lang,
                history=conversation_history,
                reference_context=general_advice["answer"],
            )
            if model_answer:
                log_query(query_clean, "ai_assistant", active_lang, 0.85, model_answer)
                return {
                    "query": query_clean,
                    "language": active_lang,
                    "routed_module": "ai_assistant",
                    "answer": model_answer,
                    "sources": general_advice.get("sources", []),
                    "structured_data": {},
                    "warning": "General agricultural guidance; confirm crop-specific actions with your local KVK."
                }
            log_query(query_clean, general_advice["routed_module"], active_lang, 0.70, general_advice["answer"])
            return {
                "query": query_clean,
                "language": active_lang,
                **general_advice,
                "structured_data": {},
                "warning": "This is general guidance. Exact timing and input recommendations depend on your crop, growth stage, soil, and district."
            }

        # 7. Use a safe diagnostic prompt when the farmer's topic is not in the local corpus.
        rag_res = rag_service.query(query_clean, top_k=3)
        reference_context = rag_res.get("grounded_answer", "") if rag_res["sufficient_evidence"] else ""
        model_answer = generative_assistant_service.answer(
            question=query_clean,
            language=active_lang,
            history=conversation_history,
            reference_context=reference_context,
        )
        if model_answer:
            log_query(query_clean, "ai_assistant", active_lang, 0.80, model_answer)
            return {
                "query": query_clean,
                "language": active_lang,
                "routed_module": "ai_assistant",
                "answer": model_answer,
                "sources": rag_res["sources"],
                "structured_data": {
                    "retrieved_chunks": rag_res["retrieved_chunks"],
                    "full_advisory": rag_res.get("grounded_answer", "") if rag_res["sufficient_evidence"] else "",
                },
                "warning": "General guidance; confirm time-sensitive or crop-specific decisions with current local agricultural advice."
            }
        if not rag_res["sufficient_evidence"]:
            answer_text = (
                "I don't have a reliable matching guide for that question in my local reference library, so I don't want to guess. "
                "Tell me your crop, district, crop stage, what you observed, when it began, and any recent rain, irrigation, "
                "fertilizer, or pesticide use. A clear photo can help with visible leaf or pest symptoms. For urgent field advice, "
                "contact your local KVK or Kisan Call Centre at 1800-180-1551."
            )
        else:
            answer_text = rag_res.get("chat_answer", rag_res["grounded_answer"])
        log_query(query_clean, "knowledge_rag", active_lang, 0.80, answer_text)
        return {
            "query": query_clean,
            "language": active_lang,
            "routed_module": "knowledge_rag",
            "answer": answer_text,
            "sources": rag_res["sources"],
            "structured_data": {"retrieved_chunks": rag_res["retrieved_chunks"], "full_advisory": rag_res.get("grounded_answer", "")},
            "warning": ("Information is grounded on indexed institutional manuals."
                        if rag_res["sufficient_evidence"] else "No matching source was found in the local agricultural knowledge base.")
        }


orchestrator_service = OrchestratorService()
