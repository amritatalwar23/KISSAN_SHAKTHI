"""Voice Assistance Service.

Speech-to-text with faster-whisper (runs locally, offline after the first model
download), answer translation into the farmer's language, and text-to-speech
with gTTS. Translation and TTS need internet; both degrade gracefully.
"""

import io
import os
import re
import tempfile
import threading
from typing import Dict, Any, Optional

from backend.app.core.logging import logger
from backend.app.services.multilingual_service import multilingual_service

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")  # Hindi / Kannada
FAST_MODEL_SIZE = "small"  # English and language detection
WHISPER_THREADS = int(os.getenv("WHISPER_THREADS", "8"))
SUPPORTED_LANGS = ["en", "kn", "hi"]
MAX_TRANSLATE_CHARS = int(os.getenv("MAX_TRANSLATE_CHARS", "900"))
NLLB_MODEL = os.getenv("NLLB_MODEL", "JustFrederik/nllb-200-distilled-600M-ct2-int8")
KANNADA_NEIGHBOURS = {"ta", "te", "ml", "si"}
NLLB_CODES = {"en": "eng_Latn", "kn": "kan_Knda", "hi": "hin_Deva"}


class VoiceService:
    def __init__(self):
        self._models = {}
        self._nllb = None
        self._cache = {}
        self._lock = threading.Lock()

    def _get_model(self, size: Optional[str] = None):
        """Loads a Whisper model once and keeps it; 'small' is fast, the large model is accurate for Indic speech."""
        size = size or WHISPER_MODEL_SIZE
        if size not in self._models:
            with self._lock:
                if size not in self._models:
                    from faster_whisper import WhisperModel
                    logger.info(f"Loading Whisper '{size}' model...")
                    self._models[size] = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=WHISPER_THREADS)
        return self._models[size]

    def warm_up(self):
        """Loads the offline translation model in the background so the first farmer request is not slow."""
        def _load():
            try:
                self._get_model(FAST_MODEL_SIZE)
                self._get_model()
                self._translate_offline("Ready.", "hi")
                logger.info("Speech and translation models warmed up.")
            except Exception as e:
                logger.warning(f"Model warm-up failed: {e}")
        threading.Thread(target=_load, daemon=True).start()

    @property
    def is_loaded(self) -> bool:
        return bool(self._models)

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribes an audio clip (wav/mp3/m4a/ogg/webm). Language hint is optional."""
        lang_hint = language if language in SUPPORTED_LANGS else None

        from faster_whisper import decode_audio

        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            audio = decode_audio(tmp_path, sampling_rate=16000)
        finally:
            os.unlink(tmp_path)

        probability = 1.0
        if lang_hint is None:
            # Whisper ranks ~100 languages; only en/kn/hi are valid here, so pick the best of those.
            _, _, all_probs = self._get_model(FAST_MODEL_SIZE).detect_language(audio)
            supported = [(lang, prob) for lang, prob in all_probs if lang in SUPPORTED_LANGS]
            lang_hint, probability = max(supported, key=lambda x: x[1]) if supported else ("en", 0.0)
            # Whisper often labels Kannada speech as a neighbouring South Indian language.
            if all_probs and all_probs[0][0] in KANNADA_NEIGHBOURS and all_probs[0][1] > probability:
                lang_hint = "kn"

        model = self._get_model(FAST_MODEL_SIZE if lang_hint == "en" else WHISPER_MODEL_SIZE)
        segments, info = model.transcribe(
            audio,
            language=lang_hint,
            beam_size=1,
            vad_filter=True,
            initial_prompt=_PROMPTS.get(lang_hint),
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        return {
            "text": text,
            "language": lang_hint,
            "language_probability": round(float(probability), 3),
            "duration_seconds": round(float(info.duration), 2),
        }

    def translate(self, text: str, target_lang: str) -> str:
        """Translates an English answer into the target language (online, glossary fallback)."""
        if target_lang == "en" or not text:
            return text
        if multilingual_service.detect_language(text) == target_lang:
            return text
        key = (text, target_lang)
        if key in self._cache:
            return self._cache[key]
        try:
            text_short = _shorten(text, MAX_TRANSLATE_CHARS)
            translated = self._translate_offline(text_short, target_lang)
            if len(self._cache) > 500:
                self._cache.clear()
            self._cache[key] = translated
            return translated
        except Exception as e:
            logger.warning(f"Offline translation failed, using glossary fallback: {e}")
            return multilingual_service.translate_text(text, target_lang, "en")["translated_text"]

    def to_english(self, text: str, source_lang: str) -> str:
        """Translates a Kannada/Hindi question to English so routing and retrieval can match the English corpus."""
        if source_lang not in ("kn", "hi") or not text.strip():
            return text
        try:
            return self._translate_offline(text, "en", source_lang)
        except Exception as e:
            logger.warning(f"Query translation to English failed: {e}")
            return text

    def _translate_offline(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """NLLB-200 (600M, int8) via CTranslate2; runs on CPU with no network after download."""
        if self._nllb is None:
            with self._lock:
                if self._nllb is None:
                    import ctranslate2
                    import transformers
                    from huggingface_hub import snapshot_download
                    path = snapshot_download(NLLB_MODEL)
                    self._nllb = (
                        ctranslate2.Translator(path, device="cpu", compute_type="int8"),
                        transformers.AutoTokenizer.from_pretrained(path, src_lang="eng_Latn"),
                    )
        translator, tokenizer = self._nllb
        target = NLLB_CODES[target_lang]
        tokenizer.src_lang = NLLB_CODES[source_lang]
        out_lines = []
        for line in text.split("\n"):
            # NLLB translates one sentence at a time best.
            sentences = [s for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
            if not sentences:
                out_lines.append(line)
                continue
            batch = [tokenizer.convert_ids_to_tokens(tokenizer.encode(s)) for s in sentences]
            results = translator.translate_batch(batch, target_prefix=[[target]] * len(batch), beam_size=2)
            out_lines.append(" ".join(
                tokenizer.decode(tokenizer.convert_tokens_to_ids(r.hypotheses[0][1:])) for r in results))
        return "\n".join(out_lines)

    def synthesize(self, text: str, language: str = "en") -> bytes:
        """Returns MP3 bytes of the text spoken in the given language."""
        from gtts import gTTS
        lang = language if language in SUPPORTED_LANGS else "en"
        spoken = _clean_for_speech(text)[:3000]
        buf = io.BytesIO()
        gTTS(text=spoken, lang=lang).write_to_fp(buf)
        return buf.getvalue()


# Domain vocabulary nudges Whisper toward farming terms.
_PROMPTS = {
    "en": "Farmer question about tomato, potato, maize, ragi, blight, leaf spot, pest, PM-KISAN, KVK.",
    "hi": "किसान का प्रश्न: टमाटर, आलू, मक्का, फसल, रोग, कीट, खाद, योजना।",
}


def _shorten(text: str, limit: int) -> str:
    """Cuts at a sentence boundary so long answers translate quickly; the English original is kept in the response."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("\n"))
    return cut[: end + 1] if end > limit * 0.5 else cut


def _clean_for_speech(text: str) -> str:
    """Strips markdown and URLs so the speech sounds natural."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_#`>|\[\]]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


voice_service = VoiceService()
