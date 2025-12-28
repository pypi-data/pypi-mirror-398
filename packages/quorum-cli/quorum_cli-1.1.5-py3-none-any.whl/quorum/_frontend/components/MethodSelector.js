import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Method selection component.
 */
import { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";
// Methods with translated names and descriptions
const getMethods = () => [
    {
        id: "standard",
        name: t("method.standard.name"),
        description: t("method.standard.desc"),
        requires: t("method.standard.requirement"),
        bestFor: t("method.standard.useCase"),
        min: 2,
        evenOnly: false,
    },
    {
        id: "oxford",
        name: t("method.oxford.name"),
        description: t("method.oxford.desc"),
        requires: t("method.oxford.requirement"),
        bestFor: t("method.oxford.useCase"),
        min: 2,
        evenOnly: true,
    },
    {
        id: "advocate",
        name: t("method.advocate.name"),
        description: t("method.advocate.desc"),
        requires: t("method.advocate.requirement"),
        bestFor: t("method.advocate.useCase"),
        min: 3,
        evenOnly: false,
    },
    {
        id: "socratic",
        name: t("method.socratic.name"),
        description: t("method.socratic.desc"),
        requires: t("method.socratic.requirement"),
        bestFor: t("method.socratic.useCase"),
        min: 2,
        evenOnly: false,
    },
    {
        id: "delphi",
        name: t("method.delphi.name"),
        description: t("method.delphi.desc"),
        requires: t("method.delphi.requirement"),
        bestFor: t("method.delphi.useCase"),
        min: 3,
        evenOnly: false,
    },
    {
        id: "brainstorm",
        name: t("method.brainstorm.name"),
        description: t("method.brainstorm.desc"),
        requires: t("method.brainstorm.requirement"),
        bestFor: t("method.brainstorm.useCase"),
        min: 2,
        evenOnly: false,
    },
    {
        id: "tradeoff",
        name: t("method.tradeoff.name"),
        description: t("method.tradeoff.desc"),
        requires: t("method.tradeoff.requirement"),
        bestFor: t("method.tradeoff.useCase"),
        min: 2,
        evenOnly: false,
    },
];
/**
 * Check if a method is compatible with the number of selected models.
 */
function isMethodCompatible(method, numModels) {
    if (numModels < method.min) {
        return { valid: false, error: t("selector.method.needsMin", { min: String(method.min) }) };
    }
    if (method.evenOnly && numModels % 2 !== 0) {
        return { valid: false, error: t("selector.method.needsEven") };
    }
    return { valid: true };
}
export function MethodSelector({ onSelect }) {
    const { discussionMethod, setDiscussionMethod, selectedModels } = useStore();
    const numModels = selectedModels.length;
    const METHODS = getMethods();
    const [selectedIndex, setSelectedIndex] = useState(METHODS.findIndex((m) => m.id === discussionMethod));
    useInput((input, key) => {
        if (key.escape) {
            onSelect(); // Just soft reload, no method change
            return;
        }
        if (key.upArrow) {
            setSelectedIndex((prev) => Math.max(0, prev - 1));
            return;
        }
        if (key.downArrow) {
            setSelectedIndex((prev) => Math.min(METHODS.length - 1, prev + 1));
            return;
        }
        if (key.return) {
            const method = METHODS[selectedIndex];
            const compat = isMethodCompatible(method, numModels);
            if (!compat.valid) {
                // Don't allow selecting incompatible method
                return;
            }
            // Set method, then soft reload
            setDiscussionMethod(method.id);
            onSelect();
            return;
        }
    });
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "magenta", paddingX: 2, paddingY: 1, children: [_jsxs(Box, { marginBottom: 1, justifyContent: "space-between", children: [_jsx(Text, { bold: true, color: "magenta", children: t("selector.method.title") }), _jsx(Text, { dimColor: true, children: t("selector.method.modelsSelected", { count: String(numModels), plural: numModels !== 1 ? "s" : "" }) })] }), METHODS.map((method, index) => {
                const isSelected = discussionMethod === method.id;
                const isCurrent = index === selectedIndex;
                const compat = isMethodCompatible(method, numModels);
                const isDisabled = !compat.valid;
                return (_jsxs(Box, { flexDirection: "column", marginBottom: index < METHODS.length - 1 ? 1 : 0, children: [_jsxs(Box, { children: [_jsx(Text, { backgroundColor: isCurrent && !isDisabled ? "magenta" : undefined, color: isDisabled ? "gray" : isCurrent ? "white" : isSelected ? "magenta" : undefined, bold: isSelected && !isDisabled, dimColor: isDisabled, children: isSelected ? "◉ " : "○ " }), _jsx(Text, { backgroundColor: isCurrent && !isDisabled ? "magenta" : undefined, color: isDisabled ? "gray" : isCurrent ? "white" : isSelected ? "magenta" : undefined, bold: (isSelected || isCurrent) && !isDisabled, dimColor: isDisabled, strikethrough: isDisabled, children: method.name }), _jsxs(Text, { backgroundColor: isCurrent && !isDisabled ? "magenta" : undefined, color: isDisabled ? "red" : isCurrent ? "white" : "yellow", dimColor: !isCurrent && !isDisabled, children: [" ", "(", isDisabled ? compat.error : method.requires, ")"] })] }), _jsx(Box, { marginLeft: 3, children: _jsx(Text, { dimColor: true, children: method.description }) }), _jsx(Box, { marginLeft: 3, children: _jsxs(Text, { dimColor: true, color: "cyan", children: ["Best for: ", method.bestFor] }) })] }, method.id));
            }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("selector.method.navigation") }) })] }));
}
