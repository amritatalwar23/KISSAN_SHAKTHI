"""Multilingual Assistance Service.

Supports English, Kannada (kn), and Hindi (hi) with language detection,
core agricultural glossary translation, and graceful fallback mechanisms.
"""

import re
from typing import Dict, Any, Optional
from backend.app.core.logging import logger

# Script detection Unicode ranges
# Kannada Unicode: 0x0C80 - 0x0CFF
# Devanagari (Hindi) Unicode: 0x0900 - 0x097F
KANNADA_REGEX = re.compile(r"[\u0C80-\u0CFF]")
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# Essential agricultural glossary for translations and terminology alignment
GLOSSARY = {
    "en": {
        "disease_detected": "Disease identified",
        "healthy_crop": "Crop is healthy",
        "advisory": "Advisory and Treatment",
        "recommended_crops": "Recommended Crops",
        "schemes": "Government Schemes",
        "expert_assistance": "Expert & KVK Assistance",
        "helpline": "Helpline",
        "disclaimer": "Notice: AI suggestions are for guidance and do not replace certified agricultural specialists."
    },
    "kn": {
        "disease_detected": "ರೋಗ ಪತ್ತೆಯಾಗಿದೆ",
        "healthy_crop": "ಬೆಳೆ ಆರೋಗ್ಯಕರವಾಗಿದೆ",
        "advisory": "ಕೃಷಿ ಸಲಹೆ ಮತ್ತು ಚಿಕಿತ್ಸೆ",
        "recommended_crops": "ಶಿಫಾರಸು ಮಾಡಿದ ಬೆಳೆಗಳು",
        "schemes": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಸಬ್ಸಿಡಿ",
        "expert_assistance": "ಕೃಷಿ ತಜ್ಞರು ಮತ್ತು ಕೆವಿಕೆ ನೆರವು",
        "helpline": "ಸಹಾಯವಾಣಿ (ಉಚಿತ ಕರೆ)",
        "disclaimer": "ಗಮನಿಸಿ: ಎಐ ಸಲಹೆಗಳು ಪ್ರಾಥಮಿಕ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಮಾತ್ರ ಮತ್ತು ಪ್ರಮಾಣೀಕೃತ ಕೃಷಿ ಅಧಿಕಾರಿಗಳಿಗೆ ಪರ್ಯಾಯವಲ್ಲ."
    },
    "hi": {
        "disease_detected": "रोग की पहचान हुई",
        "healthy_crop": "फसल स्वस्थ है",
        "advisory": "कृषि सलाह एवं उपचार",
        "recommended_crops": "अनुशंसित फसलें",
        "schemes": "सरकारी योजनाएं एवं सब्सिडी",
        "expert_assistance": "कृषि विशेषज्ञ एवं केवीके सहायता",
        "helpline": "हेल्पलाइन (टोल-फ्री)",
        "disclaimer": "सूचना: एआई सुझाव प्रारंभिक मार्गदर्शन के लिए हैं और प्रमाणित कृषि विशेषज्ञों का विकल्प नहीं हैं।"
    }
}

# Common phrase translations for query responses
COMMON_TRANSLATIONS = {
    "kn": {
        "Kisan Shakti": "ಕಿಸಾನ್ ಶಕ್ತಿ",
        "Tomato": "ಟೊಮೆಟೊ (Tomato)",
        "Potato": "ಆಲೂಗಡ್ಡೆ (Potato)",
        "Corn (Maize)": "ಮೆಕ್ಕೆಜೋಳ (Corn/Maize)",
        "Ragi (Finger Millet)": "ರಾಗಿ (Finger Millet)",
        "Early Blight": "ಮುಂಚಿನ ರೋಗ (Early Blight)",
        "Late Blight": "ತಡವಾದ ಅಂಗಮಾರಿ ರೋಗ (Late Blight)",
        "Bacterial Spot": "ಬ್ಯಾಕ್ಟೀರಿಯಾದ ಎಲೆ ಚುಕ್ಕೆ ರೋಗ (Bacterial Spot)",
        "Healthy": "ಆರೋಗ್ಯಕರ (Healthy)",
        "Tele-MANAS": "ಟೆಲಿ-ಮಾನಸ್ (Tele-MANAS: 14416)",
        "Kisan Call Centre": "ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ (KCC: 1800-180-1551)"
    },
    "hi": {
        "Kisan Shakti": "किसान शक्ति",
        "Tomato": "टमाटर (Tomato)",
        "Potato": "आलू (Potato)",
        "Corn (Maize)": "मक्का (Corn/Maize)",
        "Ragi (Finger Millet)": "रागी / मड़ुआ",
        "Early Blight": "अगेती झुलसा (Early Blight)",
        "Late Blight": "पछेती झुलसा (Late Blight)",
        "Bacterial Spot": "जीवाणु पत्ती धब्बा (Bacterial Spot)",
        "Healthy": "स्वस्थ (Healthy)",
        "Tele-MANAS": "टेली-मानस (Tele-MANAS: 14416)",
        "Kisan Call Centre": "किसान कॉल सेंटर (KCC: 1800-180-1551)"
    }
}


class MultilingualService:
    def __init__(self):
        self.supported_languages = ["en", "kn", "hi"]

    def detect_language(self, text: str) -> str:
        """Detects language script from text (Kannada, Devanagari/Hindi, or defaults to English)."""
        if not text:
            return "en"

        if KANNADA_REGEX.search(text):
            return "kn"
        elif DEVANAGARI_REGEX.search(text):
            return "hi"
        return "en"

    def translate_text(self, text: str, target_lang: str, source_lang: str = "auto") -> Dict[str, Any]:
        """Translates text to target language using curated agricultural domain mappings and rules."""
        detected = self.detect_language(text) if source_lang == "auto" else source_lang

        if target_lang not in self.supported_languages:
            logger.warning(f"Requested target language '{target_lang}' unsupported; falling back to English.")
            target_lang = "en"

        if detected == target_lang or not text:
            return {
                "original_text": text,
                "translated_text": text,
                "detected_lang": detected,
                "target_lang": target_lang
            }

        # Apply domain glossaries and phrase replacements
        translated = text
        phrase_dict = COMMON_TRANSLATIONS.get(target_lang, {})
        for eng_term, trans_term in phrase_dict.items():
            translated = re.sub(re.escape(eng_term), trans_term, translated, flags=re.IGNORECASE)

        # Prepend standard localized advisory header if target language is not English
        if target_lang == "kn":
            translated = f"[ಕನ್ನಡ ಅನುವಾದ / Kannada]: {translated}"
        elif target_lang == "hi":
            translated = f"[हिन्दी अनुवाद / Hindi]: {translated}"

        return {
            "original_text": text,
            "translated_text": translated,
            "detected_lang": detected,
            "target_lang": target_lang
        }

    def get_ui_label(self, key: str, lang: str = "en") -> str:
        """Returns localized UI string."""
        lang_dict = GLOSSARY.get(lang, GLOSSARY["en"])
        return lang_dict.get(key, GLOSSARY["en"].get(key, key))


multilingual_service = MultilingualService()
