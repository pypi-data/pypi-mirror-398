import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Synthesizer mode selection component.
 */
import { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";
// Modes will get their names from translations
const getModes = () => [
    { id: "first", name: t("synth.first.name"), description: t("synth.first.desc") },
    { id: "random", name: t("synth.random.name"), description: t("synth.random.desc") },
    { id: "rotate", name: t("synth.rotate.name"), description: t("synth.rotate.desc") },
];
export function SynthesizerSelector({ onSelect }) {
    const { synthesizerMode, setSynthesizerMode } = useStore();
    const MODES = getModes();
    const [selectedIndex, setSelectedIndex] = useState(MODES.findIndex((m) => m.id === synthesizerMode));
    useInput((input, key) => {
        if (key.escape) {
            onSelect(); // Soft reload
            return;
        }
        if (key.upArrow) {
            setSelectedIndex((prev) => Math.max(0, prev - 1));
            return;
        }
        if (key.downArrow) {
            setSelectedIndex((prev) => Math.min(MODES.length - 1, prev + 1));
            return;
        }
        if (key.return) {
            const mode = MODES[selectedIndex];
            setSynthesizerMode(mode.id);
            onSelect(); // Soft reload
            return;
        }
    });
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "cyan", paddingX: 2, paddingY: 1, children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, color: "cyan", children: t("selector.synthesizer.title") }) }), MODES.map((mode, index) => {
                const isSelected = synthesizerMode === mode.id;
                const isCurrent = index === selectedIndex;
                return (_jsxs(Box, { children: [_jsx(Text, { backgroundColor: isCurrent ? "cyan" : undefined, color: isCurrent ? "black" : isSelected ? "cyan" : undefined, bold: isSelected, children: isSelected ? "◉ " : "○ " }), _jsx(Text, { backgroundColor: isCurrent ? "cyan" : undefined, color: isCurrent ? "black" : isSelected ? "cyan" : undefined, bold: isSelected, children: mode.name.padEnd(10) }), _jsxs(Text, { backgroundColor: isCurrent ? "cyan" : undefined, color: isCurrent ? "black" : undefined, dimColor: !isCurrent, children: [" ", mode.description] })] }, mode.id));
            }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("selector.synthesizer.navigation") }) })] }));
}
