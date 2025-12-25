import { jsxs as _jsxs, jsx as _jsx, Fragment as _Fragment } from "react/jsx-runtime";
/**
 * Message display components for different message types.
 */
import React, { useMemo } from "react";
import { Box, Text } from "ink";
import { useStore } from "../store/index.js";
import { Markdown } from "../utils/markdownTerminal.js";
import { t } from "../i18n/index.js";
import { getPhaseNames } from "../utils/phases.js";
import { getModelDisplayName } from "../utils/modelName.js";
// Re-export for backward compatibility (used by Discussion.tsx)
export { getModelDisplayName } from "../utils/modelName.js";
function getProviderColor(source) {
    const s = source.toLowerCase();
    // OpenAI models
    if (s.includes("gpt") || s.includes("o1") || s.includes("o3") || s.includes("o4")) {
        return "green";
    }
    // Anthropic models
    if (s.includes("claude")) {
        return "yellow";
    }
    // Google models
    if (s.includes("gemini")) {
        return "blue";
    }
    return "white";
}
/**
 * Get border color based on debate role.
 * Takes precedence over provider color during team debates.
 */
function getRoleColor(role) {
    switch (role) {
        case "FOR":
            return "green";
        case "AGAINST":
            return "red";
        case "ADVOCATE":
            return "red"; // Devil's advocate is challenging
        case "DEFENDER":
            return "green";
        case "QUESTIONER":
            return "cyan";
        case "RESPONDENT":
            return "yellow";
        case "PANELIST":
            return "magenta"; // Delphi panelists
        case "IDEATOR":
            return "cyan"; // Brainstorm ideators
        case "EVALUATOR":
            return "blue"; // Tradeoff evaluators
        default:
            return null; // Use provider color
    }
}
/**
 * Get role badge text for display.
 */
function getRoleBadge(role) {
    switch (role) {
        case "FOR":
            return `[${t("role.for")}]`;
        case "AGAINST":
            return `[${t("role.against")}]`;
        case "ADVOCATE":
            return `[${t("role.advocate")}]`;
        case "DEFENDER":
            return `[${t("role.defender")}]`;
        case "QUESTIONER":
            return `[${t("role.questioner")}]`;
        case "RESPONDENT":
            return `[${t("role.respondent")}]`;
        case "PANELIST":
            return `[${t("role.panelist")}]`;
        case "IDEATOR":
            return `[${t("role.ideator")}]`;
        case "EVALUATOR":
            return `[${t("role.evaluator")}]`;
        default:
            return null;
    }
}
/**
 * Get round display name for Oxford mode.
 */
function getRoundLabel(roundType) {
    switch (roundType) {
        case "opening":
            return `(${t("round.opening")})`;
        case "rebuttal":
            return `(${t("round.rebuttal")})`;
        case "closing":
            return `(${t("round.closing")})`;
        default:
            return null;
    }
}
function RoundHeader({ roundType }) {
    const getLabel = (type) => {
        switch (type) {
            case "opening": return t("round.opening");
            case "rebuttal": return t("round.rebuttal");
            case "closing": return t("round.closing");
            default: return type;
        }
    };
    return (_jsx(Box, { marginY: 1, paddingX: 2, children: _jsxs(Text, { bold: true, color: "magenta", children: ["\u2550\u2550\u2550 ", getLabel(roundType), " \u2550\u2550\u2550"] }) }));
}
export function PhaseMarker({ phase, messageKey, params }) {
    const { currentMethod } = useStore();
    const PHASE_NAMES = useMemo(() => getPhaseNames(), []);
    const methodPhases = PHASE_NAMES[currentMethod] || PHASE_NAMES.standard;
    const phaseName = methodPhases[phase] || `Phase ${phase}`;
    const displayMessage = t(messageKey, params || {});
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "single", borderColor: "blue", paddingX: 2, children: [_jsxs(Text, { bold: true, color: "blue", children: ["\u2501\u2501\u2501 ", t("phase.label"), " ", phase, ": ", phaseName, " \u2501\u2501\u2501"] }), _jsx(Text, { dimColor: true, children: displayMessage })] }));
}
export function IndependentAnswer({ source, content }) {
    const color = getProviderColor(source);
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "round", borderColor: color, paddingX: 2, paddingY: 1, children: [_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { bold: true, color: color, children: source }), _jsxs(Text, { dimColor: true, children: [" ", t("msg.independentAnswer")] })] }), _jsx(Markdown, { children: content })] }));
}
export function Critique({ source, agreements, disagreements, missing }) {
    const color = getProviderColor(source);
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "round", borderColor: color, paddingX: 2, paddingY: 1, children: [_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { bold: true, color: color, children: source }), _jsxs(Text, { dimColor: true, children: [" ", t("msg.critique")] })] }), _jsxs(Box, { flexDirection: "column", children: [agreements && (_jsxs(Box, { flexDirection: "column", marginBottom: 1, children: [_jsxs(Text, { color: "green", bold: true, children: ["\u2713 ", t("msg.agreements")] }), _jsx(Box, { marginLeft: 2, children: _jsx(Markdown, { children: agreements }) })] })), disagreements && (_jsxs(Box, { flexDirection: "column", marginBottom: 1, children: [_jsxs(Text, { color: "red", bold: true, children: ["\u2717 ", t("msg.disagreements")] }), _jsx(Box, { marginLeft: 2, children: _jsx(Markdown, { children: disagreements }) })] })), missing && (_jsxs(Box, { flexDirection: "column", children: [_jsxs(Text, { color: "yellow", bold: true, children: ["? ", t("msg.missing")] }), _jsx(Box, { marginLeft: 2, children: _jsx(Markdown, { children: missing }) })] }))] })] }));
}
export function ChatMessage({ source, content, role, roundType }) {
    // Use role color if available, otherwise provider color
    const roleColor = getRoleColor(role);
    const color = roleColor || getProviderColor(source);
    const badge = getRoleBadge(role);
    const roundLabel = getRoundLabel(roundType);
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "round", borderColor: color, paddingX: 2, paddingY: 1, children: [_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { bold: true, color: color, children: source }), badge && (_jsxs(_Fragment, { children: [_jsx(Text, { children: " " }), _jsx(Text, { bold: true, color: color, children: badge })] })), roundLabel && (_jsxs(_Fragment, { children: [_jsx(Text, { children: " " }), _jsx(Text, { dimColor: true, children: roundLabel })] }))] }), _jsx(Markdown, { children: content })] }));
}
export function FinalPosition({ source, position, confidence }) {
    const color = getProviderColor(source);
    const confidenceColor = confidence === "HIGH" ? "green" : confidence === "MEDIUM" ? "yellow" : "red";
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "round", borderColor: color, paddingX: 2, paddingY: 1, children: [_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { bold: true, color: color, children: source }), _jsxs(Text, { dimColor: true, children: [" ", t("msg.finalPosition")] }), _jsx(Text, { children: " " }), _jsxs(Text, { color: confidenceColor, bold: true, children: ["[", confidence === "HIGH" ? t("msg.confidence.high") : confidence === "MEDIUM" ? t("msg.confidence.medium") : t("msg.confidence.low"), "]"] })] }), _jsx(Markdown, { children: position })] }));
}
export function Synthesis({ consensus, synthesis, differences, synthesizerModel, confidenceBreakdown, method, }) {
    const isSocratic = method === "socratic";
    const isAdvocate = method === "advocate";
    const isOxford = method === "oxford";
    const isDelphi = method === "delphi";
    const isBrainstorm = method === "brainstorm";
    const isTradeoff = method === "tradeoff";
    // Method-specific result handling
    // Oxford: FOR (green), AGAINST (red), PARTIAL (yellow)
    // Advocate: No consensus display - just show the verdict
    // Delphi: Convergence YES/PARTIAL/NO
    // Brainstorm: "X SELECTED" (count of ideas)
    // Tradeoff: Agreement YES/NO
    // Standard/Socratic: YES (green), NO (red), PARTIAL (yellow)
    const getResultColor = () => {
        if (isOxford) {
            return consensus === "FOR" ? "green"
                : consensus === "AGAINST" ? "red"
                    : "yellow";
        }
        if (isBrainstorm) {
            return "cyan"; // Always cyan for brainstorm ideas
        }
        if (isTradeoff) {
            return consensus === "YES" ? "green" : "yellow";
        }
        return consensus === "YES" ? "green"
            : consensus === "PARTIAL" ? "yellow"
                : "red";
    };
    const getResultIcon = () => {
        if (isOxford) {
            return consensus === "FOR" ? "✓ FOR"
                : consensus === "AGAINST" ? "✗ AGAINST"
                    : "◐ PARTIAL";
        }
        if (isSocratic) {
            return consensus === "YES" ? "✓"
                : consensus === "PARTIAL" ? "◐"
                    : "✗";
        }
        if (isDelphi) {
            return consensus === "YES" ? "✓"
                : consensus === "PARTIAL" ? "◐"
                    : "✗";
        }
        if (isBrainstorm) {
            return "💡"; // Light bulb for ideas
        }
        if (isTradeoff) {
            return consensus === "YES" ? "✓" : "◐";
        }
        return consensus === "YES" ? "✓"
            : consensus === "PARTIAL" ? "◐"
                : "✗";
    };
    const resultColor = getResultColor();
    // Method-specific terminology for authentic presentation
    const resultLabel = isSocratic ? t("synthesis.aporia")
        : isOxford ? t("synthesis.decision")
            : isDelphi ? t("synthesis.convergence")
                : isBrainstorm ? t("synthesis.selectedIdeas")
                    : isTradeoff ? t("synthesis.agreement")
                        : t("synthesis.consensus");
    const differencesLabel = isSocratic ? t("synthesis.openQuestions")
        : isAdvocate ? t("synthesis.unresolvedQuestions")
            : isOxford ? t("synthesis.keyContentions")
                : isDelphi ? t("synthesis.outlierPerspectives")
                    : isBrainstorm ? t("synthesis.alternativeDirections")
                        : isTradeoff ? t("synthesis.keyTradeoffs")
                            : t("synthesis.notableDifferences");
    const synthesisLabel = isSocratic ? t("synthesis.reflection")
        : isAdvocate ? t("synthesis.ruling")
            : isOxford ? t("synthesis.adjudication")
                : isDelphi ? t("synthesis.aggregatedEstimate")
                    : isBrainstorm ? t("synthesis.finalIdeas")
                        : isTradeoff ? t("synthesis.recommendation")
                            : t("synthesis.synthesisLabel");
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "double", borderColor: isAdvocate ? "red" : resultColor, paddingX: 2, paddingY: 1, children: [!isAdvocate && (_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { bold: true, color: resultColor, children: isOxford ? getResultIcon() : `${getResultIcon()} ${resultLabel}: ${consensus}` }), _jsxs(Text, { dimColor: true, children: [" ", "(", isSocratic ? t("synthesis.reflected") : isOxford ? t("synthesis.adjudicated") : t("synthesis.synthesized"), " by ", synthesizerModel, ")"] })] })), isAdvocate && (_jsxs(Box, { marginBottom: 1, children: [_jsxs(Text, { bold: true, color: "red", children: ["\u2696 ", t("msg.verdict")] }), _jsxs(Text, { dimColor: true, children: [" ", t("synthesis.ruledBy", { model: synthesizerModel })] })] })), confidenceBreakdown && (method === "standard" || method === "delphi") && (_jsxs(Box, { marginBottom: 1, children: [_jsx(Text, { dimColor: true, children: isDelphi ? t("msg.confidence.panelist") : t("msg.confidence.breakdown") }), _jsxs(Text, { color: "green", children: [t("msg.confidence.high"), ": ", confidenceBreakdown.HIGH || 0, " "] }), _jsxs(Text, { color: "yellow", children: [t("msg.confidence.medium"), ": ", confidenceBreakdown.MEDIUM || 0, " "] }), _jsxs(Text, { color: "red", children: [t("msg.confidence.low"), ": ", confidenceBreakdown.LOW || 0] })] })), _jsxs(Box, { flexDirection: "column", marginBottom: 1, children: [_jsxs(Text, { bold: true, children: [synthesisLabel, ":"] }), _jsx(Box, { marginLeft: 2, children: _jsx(Markdown, { children: synthesis }) })] }), differences && differences !== "None" && differences !== "See verdict above for unresolved questions." && (_jsxs(Box, { flexDirection: "column", children: [_jsxs(Text, { bold: true, color: "yellow", children: [differencesLabel, ":"] }), _jsx(Box, { marginLeft: 2, children: _jsx(Markdown, { children: differences }) })] }))] }));
}
// ============================================================================
// Discussion Header
// ============================================================================
const getMethodTitles = () => ({
    standard: t("discussion.standard"),
    oxford: t("discussion.oxford"),
    advocate: t("discussion.advocate"),
    socratic: t("discussion.socratic"),
    delphi: t("discussion.delphi"),
    brainstorm: t("discussion.brainstorm"),
    tradeoff: t("discussion.tradeoff"),
});
export function DiscussionHeader({ method, models, roleAssignments }) {
    const { availableModels } = useStore();
    const METHOD_TITLES = getMethodTitles();
    const getDisplayName = (modelId) => getModelDisplayName(modelId, availableModels);
    const title = METHOD_TITLES[method] || "DISCUSSION";
    // Get method-specific color
    const methodColor = method === "oxford" ? "magenta"
        : method === "advocate" ? "red"
            : method === "socratic" ? "cyan"
                : method === "delphi" ? "magenta"
                    : method === "brainstorm" ? "cyan"
                        : method === "tradeoff" ? "blue"
                            : "blue";
    // Render based on method type
    const renderParticipants = () => {
        if (!roleAssignments || Object.keys(roleAssignments).length === 0) {
            // Standard - no roles, just list participants
            return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Text, { dimColor: true, children: t("msg.participants") }), _jsx(Box, { flexDirection: "row", flexWrap: "wrap", marginTop: 1, children: models.map((model, i) => (_jsx(Box, { marginRight: 2, children: _jsxs(Text, { color: getProviderColor(model), children: ["\u25CF ", getDisplayName(model)] }) }, model))) })] }));
        }
        // Role-based methods
        const roles = Object.keys(roleAssignments);
        if (method === "socratic") {
            // Socratic: One respondent, multiple questioners
            const respondent = roleAssignments["Respondent"]?.[0];
            const questioners = roleAssignments["Questioners"] || [];
            return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { color: "yellow", bold: true, children: t("role.respondent") }) }), respondent && (_jsx(Box, { marginLeft: 2, marginBottom: 1, children: _jsxs(Text, { color: getProviderColor(respondent), children: ["\u25CF ", getDisplayName(respondent)] }) })), _jsx(Box, { marginBottom: 1, children: _jsx(Text, { color: "cyan", bold: true, children: t("role.questioner") }) }), _jsx(Box, { marginLeft: 2, flexDirection: "column", children: questioners.map((model) => (_jsxs(Text, { color: getProviderColor(model), children: ["\u25CF ", getDisplayName(model)] }, model))) })] }));
        }
        // Oxford/Advocate: Two columns
        // Note: Keys match TeamPreview format - Oxford uses "FOR"/"AGAINST", Advocate uses "Defenders"/"Advocate"
        const leftRole = method === "oxford" ? "FOR" : "Defenders";
        const rightRole = method === "oxford" ? "AGAINST" : "Advocate";
        const leftLabel = method === "oxford" ? t("team.forTeam") : t("team.defenders");
        const rightLabel = method === "oxford" ? t("team.againstTeam") : t("role.advocate");
        const leftColor = "green";
        const rightColor = "red";
        const leftModels = roleAssignments[leftRole] || [];
        const rightModels = roleAssignments[rightRole] || [];
        return (_jsxs(Box, { children: [_jsxs(Box, { flexDirection: "column", width: "50%", children: [_jsx(Text, { color: leftColor, bold: true, children: leftLabel }), _jsx(Box, { marginLeft: 2, marginTop: 1, flexDirection: "column", children: leftModels.map((model) => (_jsxs(Text, { color: getProviderColor(model), children: ["\u25CF ", getDisplayName(model)] }, model))) })] }), _jsxs(Box, { flexDirection: "column", width: "50%", children: [_jsx(Text, { color: rightColor, bold: true, children: rightLabel }), _jsx(Box, { marginLeft: 2, marginTop: 1, flexDirection: "column", children: rightModels.map((model) => (_jsxs(Text, { color: getProviderColor(model), children: ["\u25CF ", getDisplayName(model)] }, model))) })] })] }));
    };
    return (_jsxs(Box, { flexDirection: "column", marginY: 1, borderStyle: "double", borderColor: methodColor, paddingX: 2, paddingY: 1, children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, color: methodColor, children: title }) }), renderParticipants()] }));
}
/**
 * Memoized Message component to prevent unnecessary re-renders.
 * Only re-renders when the message prop actually changes.
 */
export const Message = React.memo(function Message({ message }) {
    const { availableModels } = useStore();
    // Get display name for any model source
    const getDisplayName = (modelId) => getModelDisplayName(modelId, availableModels);
    switch (message.type) {
        case "phase":
            return (_jsx(PhaseMarker, { phase: message.phase || 0, messageKey: message.phaseMessageKey || "", params: message.phaseParams }));
        case "answer":
            return (_jsx(IndependentAnswer, { source: getDisplayName(message.source || ""), content: message.content || "" }));
        case "critique":
            return (_jsx(Critique, { source: getDisplayName(message.source || ""), agreements: message.agreements || "", disagreements: message.disagreements || "", missing: message.missing || "" }));
        case "chat":
            return (_jsx(ChatMessage, { source: getDisplayName(message.source || ""), content: message.content || "", role: message.role, roundType: message.roundType }));
        case "round_header":
            return (_jsx(RoundHeader, { roundType: message.roundType }));
        case "position":
            return (_jsx(FinalPosition, { source: getDisplayName(message.source || ""), position: message.position || "", confidence: message.confidence || "MEDIUM" }));
        case "synthesis":
            return (_jsx(Synthesis, { consensus: message.consensus || "PARTIAL", synthesis: message.synthesis || "", differences: message.differences || "None", synthesizerModel: getDisplayName(message.synthesizerModel || ""), confidenceBreakdown: message.confidenceBreakdown, method: message.method }));
        case "discussion_header":
            return (_jsx(DiscussionHeader, { method: message.headerMethod || "standard", models: message.headerModels || [], roleAssignments: message.headerRoleAssignments }));
        default:
            return null;
    }
});
