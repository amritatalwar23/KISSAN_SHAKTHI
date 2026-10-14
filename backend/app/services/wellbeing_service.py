"""Farmer Wellbeing and Crisis Support Module.

Provides safety-bounded, empathetic detection of distress signals and connects farmers
with verified, free national crisis response helplines (Tele-MANAS, Kisan Call Centre, KIRAN).
Does not attempt psychiatric diagnosis or replace clinical emergency services.
"""

import re
from typing import Dict, Any, List
from backend.app.core.logging import logger


VERIFIED_HELPLINES = [
    {
        "name": "Tele-MANAS (National Tele Mental Health Programme)",
        "number": "14416 / 1800-891-4416",
        "availability": "24 hours a day, 7 days a week (365 days)",
        "languages": "English, Kannada, Hindi, Telugu, Tamil, and 15+ Indian languages",
        "managed_by": "Ministry of Health and Family Welfare, Govt of India (NIMHANS apex center)",
        "is_toll_free": True
    },
    {
        "name": "Kisan Call Centre (KCC)",
        "number": "1800-180-1551",
        "availability": "6:00 AM to 10:00 PM, all 7 days of the week",
        "languages": "Kannada, Hindi, English, and regional state languages",
        "managed_by": "Department of Agriculture & Farmers Welfare, Ministry of Agriculture",
        "is_toll_free": True
    },
    {
        "name": "KIRAN National Mental Health Helpline",
        "number": "1800-599-0019",
        "availability": "24 hours a day, 7 days a week",
        "languages": "Hindi, English, Kannada, Marathi, Tamil, and 8 other languages",
        "managed_by": "Department of Empowerment of Persons with Disabilities, Govt of India",
        "is_toll_free": True
    }
]

# Conservative patterns for distress and acute crisis signals (Unicode-aware for Indic scripts)
HIGH_CRISIS_KEYWORDS = [
    r"\bsuicid(e|al)\b",
    r"\bend(ing)?\s+my\s+life\b",
    r"\bkill(ing)?\s+myself\b",
    r"\bwant\s+to\s+die\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bbetter\s+off\s+dead\b",
    r"\bhanging\s+myself\b",
    r"\bdrink(ing)?\s+poison\b",
    r"\bconsume(d)?\s+pesticide\b",
    r"ಆತ್ಮಹತ್ಯೆ",          # Kannada for suicide
    r"ಸಾಯಲು\s+ಬಯಸುತ್ತೇನೆ", # Kannada: want to die
    r"ಜೀವ\s+ತೆಗೆದುಕೊಳ್ಳ", # Kannada: take life
    r"आत्महत्या",          # Hindi for suicide
    r"मरना\s+चाहता",        # Hindi: want to die
    r"जान\s+दे",           # Hindi: give life
    r"जहर\s+खा"            # Hindi: take poison
]

ELEVATED_DISTRESS_KEYWORDS = [
    r"\bdeep\s+debt\b",
    r"\bloan\s+burden\b",
    r"\blost\s+everything\b",
    r"\bcrop\s+failure.*ruined\b",
    r"\bhopeless\b",
    r"\bdepressed\b",
    r"\bcannot\s+bear\s+this\b",
    r"\bcan\'?t\s+take\s+it\s+anymore\b",
    r"ಸಾಲದ\s+ಹೊರೆ",     # Kannada: debt burden
    r"ಬೆಳೆ\s+ನಾಶ",       # Kannada: crop loss
    r"कर्ज",            # Hindi: debt
    r"फसल\s+बर्बाद"      # Hindi: crop destroyed
]


class WellbeingService:
    def __init__(self):
        self.high_crisis_patterns = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in HIGH_CRISIS_KEYWORDS]
        self.elevated_distress_patterns = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in ELEVATED_DISTRESS_KEYWORDS]

    def assess_wellbeing(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Detects whether user text conveys severe crisis, acute distress, or standard query."""
        if not text or len(text.strip()) == 0:
            return {
                "is_crisis_detected": False,
                "urgency_level": "normal",
                "empathetic_message": "How can we assist you with your farming needs today?",
                "helplines": [],
                "safety_disclaimer": "Kisan Shakti is an agricultural information service."
            }

        # Check for immediate life-safety crisis
        for pattern in self.high_crisis_patterns:
            if pattern.search(text):
                logger.warning("Urgent crisis distress signal detected in query.")
                return {
                    "is_crisis_detected": True,
                    "urgency_level": "immediate_crisis",
                    "empathetic_message": (
                        "We hear how overwhelming and painful this situation feels right now, "
                        "but please know you do not have to carry this heavy burden alone. "
                        "Your life is precious, and compassionate people are available right now "
                        "to listen, help, and guide you through this difficult time. "
                        "Please reach out immediately to the free, confidential 24x7 support helplines below, "
                        "or speak with a trusted family member or elder in your community."
                    ),
                    "helplines": VERIFIED_HELPLINES,
                    "safety_disclaimer": (
                        "EMERGENCY ASSISTANCE: If you or someone you know is in immediate danger, "
                        "please dial 112 (National Emergency Helpline) or call Tele-MANAS at 14416 immediately. "
                        "Kisan Shakti cannot provide clinical mental health interventions."
                    )
                }

        # Check for elevated farming distress (debt/crop loss despair)
        for pattern in self.elevated_distress_patterns:
            if pattern.search(text):
                return {
                    "is_crisis_detected": True,
                    "urgency_level": "elevated",
                    "empathetic_message": (
                        "Farming carries immense challenges, and dealing with crop loss or financial distress "
                        "is deeply stressful. Please remember that support, relief schemes, and debt counseling are available. "
                        "You can speak with agricultural counselors who understand farming hardships."
                    ),
                    "helplines": [VERIFIED_HELPLINES[1], VERIFIED_HELPLINES[0]],
                    "safety_disclaimer": (
                        "Kisan Shakti provides informational assistance. For emotional wellbeing and institutional relief support, "
                        "please connect with the free helplines listed above."
                    )
                }

        # Normal query
        return {
            "is_crisis_detected": False,
            "urgency_level": "normal",
            "empathetic_message": "We are here to support your farming decisions.",
            "helplines": [],
            "safety_disclaimer": "Agricultural assistance provided by Kisan Shakti."
        }


wellbeing_service = WellbeingService()
