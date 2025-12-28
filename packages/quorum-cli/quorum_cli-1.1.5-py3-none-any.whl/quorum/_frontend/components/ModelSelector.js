import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Model selection component.
 */
import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";
export function ModelSelector({ onSelect }) {
    const { availableModels, selectedModels, toggleSelectedModel, validatedModels, invalidModels, } = useStore();
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [confirming, setConfirming] = useState(false);
    // Flatten models into a list
    const allModels = [];
    for (const [provider, models] of Object.entries(availableModels)) {
        for (const model of models) {
            allModels.push({ provider, model });
        }
    }
    useInput((input, key) => {
        if (key.escape) {
            if (confirming) {
                setConfirming(false);
            }
            else {
                onSelect(); // Soft reload
            }
            return;
        }
        if (key.upArrow) {
            setSelectedIndex((prev) => Math.max(0, prev - 1));
            return;
        }
        if (key.downArrow) {
            setSelectedIndex((prev) => Math.min(allModels.length - 1, prev + 1));
            return;
        }
        if (input === " " && allModels.length > 0) {
            const modelId = allModels[selectedIndex].model.id;
            // Only allow toggling validated models
            if (validatedModels.has(modelId)) {
                toggleSelectedModel(modelId);
            }
            return;
        }
        if (key.return) {
            if (selectedModels.length >= 2) {
                onSelect(); // Models already saved in store, just soft reload
            }
            else {
                setConfirming(true);
            }
            return;
        }
    });
    if (allModels.length === 0) {
        return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "red", paddingX: 2, paddingY: 1, children: [_jsx(Text, { bold: true, color: "red", children: t("selector.model.noModels") }), _jsx(Text, { dimColor: true, children: t("selector.model.checkApi") })] }));
    }
    let currentProvider = "";
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "cyan", paddingX: 2, paddingY: 1, children: [_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { bold: true, color: "cyan", children: t("selector.model.title") }), _jsxs(Text, { dimColor: true, children: [" ", t("selector.model.instructions")] })] }), _jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { children: t("selector.model.selected") }), _jsx(Text, { color: selectedModels.length >= 2 ? "green" : "yellow", bold: true, children: selectedModels.length }), _jsxs(Text, { dimColor: true, children: [" ", t("selector.model.minimum")] })] }), allModels.map((item, index) => {
                const modelId = item.model.id;
                const isSelected = selectedModels.includes(modelId);
                const isCurrent = index === selectedIndex;
                const isValid = validatedModels.has(modelId);
                const error = invalidModels[modelId];
                const isDisabled = !isValid;
                // Provider header
                let providerHeader = null;
                if (item.provider !== currentProvider) {
                    currentProvider = item.provider;
                    providerHeader = (_jsx(Box, { marginTop: index > 0 ? 1 : 0, children: _jsx(Text, { bold: true, color: "blue", children: item.provider.toUpperCase() }) }, `provider-${item.provider}`));
                }
                return (_jsxs(React.Fragment, { children: [providerHeader, _jsxs(Box, { children: [_jsx(Text, { backgroundColor: isCurrent ? "blue" : undefined, color: isDisabled ? "gray" : isCurrent ? "white" : undefined, dimColor: isDisabled, children: isSelected ? "◉ " : "○ " }), _jsx(Text, { backgroundColor: isCurrent ? "blue" : undefined, color: error
                                        ? "red"
                                        : isDisabled
                                            ? "gray"
                                            : isSelected
                                                ? "green"
                                                : isCurrent
                                                    ? "white"
                                                    : undefined, bold: isSelected && !isDisabled, dimColor: isDisabled && !error, children: item.model.display_name || modelId }), error && _jsxs(Text, { color: "red", children: [" \u2717 ", error] }), isSelected && isValid && _jsx(Text, { color: "green", children: " \u2713" })] })] }, modelId));
            }), confirming && selectedModels.length < 2 && (_jsx(Box, { marginTop: 1, children: _jsxs(Text, { color: "yellow", children: ["\u26A0 ", t("selector.model.warning")] }) })), _jsx(Box, { marginTop: 1, flexDirection: "column", children: _jsx(Text, { dimColor: true, children: t("selector.model.navigation") }) })] }));
}
