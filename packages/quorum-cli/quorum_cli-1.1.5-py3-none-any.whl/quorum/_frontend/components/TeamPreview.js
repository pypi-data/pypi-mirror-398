import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
/**
 * Team assignment preview for Oxford/Advocate/Socratic modes.
 * Shows role assignments before debate starts and allows customization.
 */
import { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { getModelDisplayName } from "./Message.js";
import { t } from "../i18n/index.js";
/**
 * Get the "special" role for a method (the one that can be selected).
 */
function getSpecialRole(method) {
    if (method === "advocate")
        return "Advocate";
    if (method === "socratic")
        return "Respondent";
    return null;
}
/**
 * Get all models from assignments as a flat list.
 */
function getAllModels(assignments) {
    return Object.values(assignments).flat();
}
/**
 * Rebuild assignments with a new special role model.
 */
function setSpecialRoleModel(method, allModels, specialModel) {
    if (method === "advocate") {
        const defenders = allModels.filter(m => m !== specialModel);
        return { "Defenders": defenders, "Advocate": [specialModel] };
    }
    if (method === "socratic") {
        const questioners = allModels.filter(m => m !== specialModel);
        return { "Respondent": [specialModel], "Questioners": questioners };
    }
    return {};
}
export function TeamPreview({ assignments, method, onConfirm, onCancel }) {
    const { availableModels } = useStore();
    const [currentAssignments, setCurrentAssignments] = useState(assignments);
    const specialRole = getSpecialRole(method);
    const allModels = getAllModels(assignments);
    const isOxford = method === "oxford";
    // For Oxford: button selection (start/swap)
    // For Advocate/Socratic: model selection
    const [selectedIndex, setSelectedIndex] = useState(0);
    const getDisplayName = (modelId) => getModelDisplayName(modelId, availableModels);
    // Get current special model (for Advocate/Socratic)
    const currentSpecialModel = specialRole
        ? currentAssignments[specialRole]?.[0]
        : null;
    useInput((input, key) => {
        if (key.escape) {
            onCancel();
            return;
        }
        if (isOxford) {
            // Oxford mode: swap teams
            if (key.leftArrow || key.rightArrow) {
                setSelectedIndex(prev => prev === 0 ? 1 : 0);
                return;
            }
            if (key.return) {
                if (selectedIndex === 0) {
                    onConfirm(currentAssignments);
                }
                else {
                    // Swap FOR/AGAINST
                    setCurrentAssignments({
                        "FOR": currentAssignments["AGAINST"],
                        "AGAINST": currentAssignments["FOR"],
                    });
                }
                return;
            }
            if (input === "s" || input === "S") {
                setCurrentAssignments({
                    "FOR": currentAssignments["AGAINST"],
                    "AGAINST": currentAssignments["FOR"],
                });
                return;
            }
        }
        else {
            // Advocate/Socratic mode: select model for special role
            if (key.upArrow) {
                setSelectedIndex(prev => Math.max(0, prev - 1));
                return;
            }
            if (key.downArrow) {
                setSelectedIndex(prev => Math.min(allModels.length, prev + 1));
                return;
            }
            if (key.return) {
                if (selectedIndex === allModels.length) {
                    // Start button
                    onConfirm(currentAssignments);
                }
                else {
                    // Select this model as special role
                    const newSpecial = allModels[selectedIndex];
                    const newAssignments = setSpecialRoleModel(method, allModels, newSpecial);
                    setCurrentAssignments(newAssignments);
                }
                return;
            }
        }
    });
    const roles = Object.entries(currentAssignments);
    // Determine role color
    const getRoleColor = (role) => {
        if (role === "FOR" || role === "Defenders")
            return "green";
        if (role === "AGAINST" || role === "Advocate")
            return "red";
        if (role === "Respondent")
            return "cyan";
        if (role === "Questioners" || role === "Questioner")
            return "yellow";
        if (role === "Panelists")
            return "magenta";
        if (role === "Ideators")
            return "cyan";
        if (role === "Evaluators")
            return "blue";
        return "white";
    };
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "blue", paddingX: 2, paddingY: 1, children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, color: "blue", children: isOxford ? t("team.title") : t("team.selectRole", { role: specialRole || "" }) }) }), isOxford ? (
            // Oxford: Show teams
            _jsxs(_Fragment, { children: [roles.map(([role, models]) => (_jsxs(Box, { marginBottom: 1, children: [_jsxs(Text, { bold: true, color: getRoleColor(role), children: [role, ":"] }), _jsx(Text, { children: " " }), _jsx(Text, { children: models.map(getDisplayName).join(", ") })] }, role))), _jsxs(Box, { marginTop: 1, gap: 2, children: [_jsx(Box, { children: _jsx(Text, { backgroundColor: selectedIndex === 0 ? "blue" : undefined, color: selectedIndex === 0 ? "white" : "blue", bold: selectedIndex === 0, children: " " + t("team.start") + " " }) }), _jsx(Box, { children: _jsx(Text, { backgroundColor: selectedIndex === 1 ? "blue" : undefined, color: selectedIndex === 1 ? "white" : "blue", bold: selectedIndex === 1, children: " " + t("team.swap") + " " }) })] }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("team.navigationOxford") }) })] })) : (
            // Advocate/Socratic: Select model for special role
            _jsxs(_Fragment, { children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { dimColor: true, children: method === "advocate"
                                ? t("team.chooseAdvocate")
                                : t("team.chooseRespondent") }) }), allModels.map((modelId, index) => {
                        const isSpecial = modelId === currentSpecialModel;
                        const isCursor = index === selectedIndex;
                        return (_jsx(Box, { children: _jsxs(Text, { backgroundColor: isCursor ? "blue" : undefined, color: isCursor ? "white" : isSpecial ? getRoleColor(specialRole) : undefined, bold: isSpecial, children: [isSpecial ? "● " : "○ ", getDisplayName(modelId), isSpecial && _jsxs(Text, { color: isCursor ? "white" : "gray", children: [" (", specialRole, ")"] })] }) }, modelId));
                    }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { backgroundColor: selectedIndex === allModels.length ? "blue" : undefined, color: selectedIndex === allModels.length ? "white" : "green", bold: selectedIndex === allModels.length, children: " " + t("team.start") + " " }) }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("team.navigation") }) })] }))] }));
}
