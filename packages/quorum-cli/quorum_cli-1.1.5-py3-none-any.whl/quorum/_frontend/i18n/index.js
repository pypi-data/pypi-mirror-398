/**
 * Internationalization (i18n) module for Quorum frontend.
 *
 * Supports 6 languages: English, Swedish, German, French, Spanish, Italian.
 * Language is determined by QUORUM_DEFAULT_LANGUAGE setting.
 */
import { en } from "./translations/en.js";
import { sv } from "./translations/sv.js";
import { de } from "./translations/de.js";
import { fr } from "./translations/fr.js";
import { es } from "./translations/es.js";
import { it } from "./translations/it.js";
// All available translations
const translations = {
    en,
    sv,
    de,
    fr,
    es,
    it,
};
// Current language (defaults to English)
let currentLanguage = "en";
/**
 * Map language string to supported language code.
 * Handles various formats: "Swedish", "sv", "swedish", etc.
 */
function mapLanguageToCode(lang) {
    if (!lang)
        return "en";
    const normalized = lang.toLowerCase().trim();
    // Direct code matches
    if (normalized in translations) {
        return normalized;
    }
    // Full name matches
    const nameMap = {
        english: "en",
        swedish: "sv",
        svenska: "sv",
        german: "de",
        deutsch: "de",
        french: "fr",
        francais: "fr",
        spanish: "es",
        espanol: "es",
        italian: "it",
        italiano: "it",
    };
    return nameMap[normalized] || "en";
}
/**
 * Set the current language.
 * Call this when config is loaded from backend.
 */
export function setLanguage(lang) {
    currentLanguage = mapLanguageToCode(lang);
}
/**
 * Get the current language code.
 */
export function getLanguage() {
    return currentLanguage;
}
/**
 * Translate a key with optional parameter interpolation.
 *
 * @param key - Translation key
 * @param params - Parameters to interpolate (e.g., { model: "GPT-4o" })
 * @returns Translated string
 *
 * @example
 * t("thinkingComplete", { model: "GPT-4o" })
 * // → "GPT-4o finished thinking" (en)
 * // → "GPT-4o har tankt klart" (sv)
 */
export function t(key, params) {
    let text = translations[currentLanguage]?.[key] || translations.en[key] || key;
    if (params) {
        Object.entries(params).forEach(([k, v]) => {
            text = text.replace(new RegExp(`\\{${k}\\}`, "g"), v);
        });
    }
    return text;
}
