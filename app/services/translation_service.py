"""
Translation Service - Legal Document Translation

Provides translation from English to regional Indian languages
with accurate legal terminology.

Supported Languages:
- English (en) - Default, no translation
- Kannada (kn) - ಕನ್ನಡ
- Hindi (hi) - हिंदी
"""
from typing import Optional, Dict
from app.infrastructure.llm_providers import get_llm_provider
from app.core.logging import logger


# Supported languages with their display names
SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "native": "English"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ"},
    "hi": {"name": "Hindi", "native": "हिंदी"},
}


# Legal terminology reference for accurate translations
LEGAL_TERMS_REFERENCE = """
Key legal terms and their accurate translations:

ENGLISH → KANNADA → HINDI
Court → ನ್ಯಾಯಾಲಯ → न्यायालय
High Court → ಉಚ್ಚ ನ್ಯಾಯಾಲಯ → उच्च न्यायालय
Supreme Court → ಸರ್ವೋಚ್ಚ ನ್ಯಾಯಾಲಯ → सर्वोच्च न्यायालय
District Court → ಜಿಲ್ಲಾ ನ್ಯಾಯಾಲಯ → जिला न्यायालय
Judge → ನ್ಯಾಯಾಧೀಶರು → न्यायाधीश
Plaintiff → ವಾದಿ → वादी
Defendant → ಪ್ರತಿವಾದಿ → प्रतिवादी
Appellant → ಮೇಲ್ಮನವಿದಾರ → अपीलकर्ता
Respondent → ಪ್ರತ್ಯರ್ಥಿ → प्रत्यर्थी
Petitioner → ಅರ್ಜಿದಾರ → याचिकाकर्ता
Advocate/Lawyer → ವಕೀಲ → अधिवक्ता/वकील
Affidavit → ಪ್ರಮಾಣಪತ್ರ → शपथ पत्र
Appeal → ಮೇಲ್ಮನವಿ → अपील
Bail → ಜಾಮೀನು → जमानत
Case → ಪ್ರಕರಣ → मुकदमा/वाद
Complaint → ದೂರು → शिकायत
Decree → ತೀರ್ಪು/ಡಿಕ್ರಿ → डिक्री/आज्ञप्ति
Evidence → ಸಾಕ್ಷ್ಯ → साक्ष्य/सबूत
FIR (First Information Report) → ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ → प्रथम सूचना रिपोर्ट
Hearing → ವಿಚಾರಣೆ → सुनवाई
Injunction → ನಿಷೇಧಾಜ್ಞೆ → निषेधाज्ञा
Judgment → ತೀರ್ಪು → निर्णय/फैसला
Jurisdiction → ನ್ಯಾಯವ್ಯಾಪ್ತಿ → क्षेत्राधिकार
Notice → ನೋಟೀಸು/ಸೂಚನೆ → नोटिस/सूचना
Order → ಆದೇಶ → आदेश
Penalty → ದಂಡ → जुर्माना/दंड
Petition → ಅರ್ಜಿ → याचिका
Property → ಆಸ್ತಿ → संपत्ति
Registration → ನೋಂದಣಿ → पंजीकरण
Section → ಕಲಮು/ಸೆಕ್ಷನ್ → धारा
Suit → ದಾವೆ → वाद
Summons → ಸಮನ್ಸ್ → समन
Trial → ವಿಚಾರಣೆ → मुकदमा/परीक्षण
Verdict → ತೀರ್ಪು → फैसला
Warrant → ವಾರಂಟ್ → वारंट
Witness → ಸಾಕ್ಷಿ → गवाह/साक्षी

Legal Codes:
CPC (Code of Civil Procedure) → ಸಿವಿಲ್ ಪ್ರಕ್ರಿಯಾ ಸಂಹಿತೆ → सिविल प्रक्रिया संहिता
CrPC (Code of Criminal Procedure) → ಅಪರಾಧ ಪ್ರಕ್ರಿಯಾ ಸಂಹಿತೆ → दंड प्रक्रिया संहिता
IPC (Indian Penal Code) → ಭಾರತೀಯ ದಂಡ ಸಂಹಿತೆ → भारतीय दंड संहिता
RERA → ರಿಯಲ್ ಎಸ್ಟೇಟ್ ನಿಯಂತ್ರಣ ಪ್ರಾಧಿಕಾರ → रियल एस्टेट विनियामक प्राधिकरण
"""


def get_translation_prompt(target_lang: str) -> str:
    """
    Get the translation prompt for a specific language.
    
    Args:
        target_lang: Target language code ('kn' or 'hi')
        
    Returns:
        System prompt for translation
    """
    lang_name = SUPPORTED_LANGUAGES.get(target_lang, {}).get("name", "Hindi")
    
    return f"""You are an expert legal translator specializing in Indian civil and construction law.

Your task is to translate English legal text to {lang_name} with PERFECT ACCURACY.

CRITICAL TRANSLATION RULES:

1. TRANSLATE ALL LEGAL TERMS accurately using standard legal vocabulary:
{LEGAL_TERMS_REFERENCE}

2. For Section numbers like "Section 96" or "धारा 96" (Hindi) / "ಕಲಮು 96" (Kannada):
   - Translate "Section" to the correct legal term
   - Keep the number as-is

3. For acronyms like CPC, RERA, FIR:
   - Provide the full translated name on first use
   - Example: "RERA (रियल एस्टेट विनियामक प्राधिकरण)" for Hindi

4. PRESERVE ALL FORMATTING:
   - Keep headers, bullet points, numbered lists
   - Maintain paragraph structure
   - Keep any markdown formatting

5. Use FORMAL/OFFICIAL legal language, not colloquial translations

6. Do NOT add explanations, notes, or commentary

7. If a term has no standard translation, transliterate it in the target script

OUTPUT: Only the translated text, nothing else."""


def translate_text(
    text: str,
    target_lang: str,
    llm_provider=None
) -> str:
    """
    Translate text to target language using LLM.
    
    Args:
        text: English text to translate
        target_lang: Target language code ('en', 'kn', 'hi')
        llm_provider: Optional LLM provider instance
        
    Returns:
        Translated text (or original if target is English)
    """
    # No translation needed for English
    if target_lang == "en" or target_lang not in SUPPORTED_LANGUAGES:
        return text
    
    # Skip translation for empty or very short text
    if not text or len(text.strip()) < 10:
        return text
    
    logger.info(f"Translating to {SUPPORTED_LANGUAGES[target_lang]['name']}...")
    
    # Get LLM provider
    provider = llm_provider or get_llm_provider()
    
    # Build translation messages
    system_prompt = get_translation_prompt(target_lang)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Translate the following legal text to {SUPPORTED_LANGUAGES[target_lang]['name']}:\n\n{text}"}
    ]
    
    try:
        translated = provider.chat(messages, temperature=0.3)  # Lower temperature for accuracy
        logger.success(f"Translation complete ({len(translated)} chars)")
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        # Return original text on failure
        return text


def get_supported_languages() -> Dict[str, Dict[str, str]]:
    """
    Get dictionary of supported languages.
    
    Returns:
        Dict mapping language codes to name info
    """
    return SUPPORTED_LANGUAGES.copy()


def is_supported_language(lang_code: str) -> bool:
    """
    Check if a language code is supported.
    
    Args:
        lang_code: Language code to check
        
    Returns:
        True if supported
    """
    return lang_code in SUPPORTED_LANGUAGES
