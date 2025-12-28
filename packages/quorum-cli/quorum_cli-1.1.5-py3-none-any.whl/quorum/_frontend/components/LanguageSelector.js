import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Language selector modal component.
 * Allows user to select response language for AI models.
 */
import { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { t, setLanguage } from "../i18n/index.js";
const LANGUAGES = [
    { code: "en", flag: "🇬🇧", nativeName: "English" },
    { code: "sv", flag: "🇸🇪", nativeName: "Svenska" },
    { code: "de", flag: "🇩🇪", nativeName: "Deutsch" },
    { code: "fr", flag: "🇫🇷", nativeName: "Français" },
    { code: "es", flag: "🇪🇸", nativeName: "Español" },
    { code: "it", flag: "🇮🇹", nativeName: "Italiano" },
];
export function LanguageSelector({ onClose }) {
    const { responseLanguage, setResponseLanguage } = useStore();
    const currentIndex = LANGUAGES.findIndex((l) => l.code === responseLanguage);
    const [selectedIndex, setSelectedIndex] = useState(currentIndex >= 0 ? currentIndex : 0);
    useInput((input, key) => {
        if (key.escape) {
            onClose();
            return;
        }
        if (key.upArrow) {
            setSelectedIndex((i) => (i > 0 ? i - 1 : LANGUAGES.length - 1));
            return;
        }
        if (key.downArrow) {
            setSelectedIndex((i) => (i < LANGUAGES.length - 1 ? i + 1 : 0));
            return;
        }
        if (key.return) {
            const selected = LANGUAGES[selectedIndex];
            setResponseLanguage(selected.code);
            // Also update UI language
            setLanguage(selected.code);
            onClose();
        }
    });
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "cyan", paddingX: 2, paddingY: 1, children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, color: "cyan", children: t("selector.language.title") }) }), LANGUAGES.map((lang, index) => {
                const isSelected = lang.code === responseLanguage;
                const isCurrent = index === selectedIndex;
                return (_jsxs(Box, { children: [_jsx(Text, { backgroundColor: isCurrent ? "cyan" : undefined, color: isCurrent ? "black" : isSelected ? "cyan" : undefined, bold: isSelected, children: isSelected ? "◉ " : "○ " }), _jsxs(Text, { backgroundColor: isCurrent ? "cyan" : undefined, color: isCurrent ? "black" : isSelected ? "cyan" : undefined, bold: isSelected, children: [lang.flag, " ", lang.nativeName.padEnd(10)] })] }, lang.code));
            }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("selector.language.navigation") }) })] }));
}
