/**
 * Internationalization (i18n) module for Quorum frontend.
 *
 * Supports 6 languages: English, Swedish, German, French, Spanish, Italian.
 * Language is determined by QUORUM_DEFAULT_LANGUAGE setting.
 */
import type { TranslationKey, SupportedLanguage } from "./types.js";
/**
 * Set the current language.
 * Call this when config is loaded from backend.
 */
export declare function setLanguage(lang: string | null | undefined): void;
/**
 * Get the current language code.
 */
export declare function getLanguage(): SupportedLanguage;
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
export declare function t(key: TranslationKey, params?: Record<string, string>): string;
export type { TranslationKey, Translations, SupportedLanguage } from "./types.js";
