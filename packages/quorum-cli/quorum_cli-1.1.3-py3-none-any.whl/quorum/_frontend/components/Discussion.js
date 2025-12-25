import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Discussion view showing all messages.
 */
import { useEffect, useMemo } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { Message, getModelDisplayName } from "./Message.js";
import { t } from "../i18n/index.js";
import { getPhaseNames } from "../utils/phases.js";
import { useTerminalSpinner } from "../hooks/useSpinner.js";
export function Discussion() {
    const { messages, currentQuestion, isDiscussionRunning, isDiscussionComplete, currentPhase, previousPhase, nextPhase, currentMethod, isPaused, thinkingModel, completedThinking, availableModels, resumeDiscussion, resumeBackend, } = useStore();
    // Get display name for thinking model (memoized to prevent re-computation)
    const thinkingDisplayName = useMemo(() => thinkingModel ? getModelDisplayName(thinkingModel, availableModels) : "", [thinkingModel, availableModels]);
    // Handle Enter/Space to continue when paused
    useInput(async (input, key) => {
        if (isPaused && (key.return || input === " ")) {
            // Signal backend to continue to next phase
            if (resumeBackend) {
                await resumeBackend();
            }
            // Update UI state
            resumeDiscussion();
        }
    });
    // Get phase name based on current method
    const PHASE_NAMES = getPhaseNames();
    const methodPhases = PHASE_NAMES[currentMethod] || PHASE_NAMES.standard;
    const phaseName = methodPhases[currentPhase] || `Phase ${currentPhase}`;
    const previousPhaseName = methodPhases[previousPhase] || `Phase ${previousPhase}`;
    const nextPhaseName = methodPhases[nextPhase] || `Phase ${nextPhase}`;
    // Thinking spinner text
    const thinkingText = useMemo(() => t("thinkingInProgress", { model: thinkingDisplayName }), [thinkingDisplayName]);
    // Phase progress spinner text
    const phaseProgressText = useMemo(() => currentPhase === 0
        ? t("msg.startingDiscussion")
        : t("msg.phaseInProgress", { phase: String(currentPhase), name: phaseName }), [currentPhase, phaseName]);
    // Thinking spinner (yellow) - shows when a model is thinking
    useTerminalSpinner({
        text: thinkingText,
        color: "yellow",
        active: !!thinkingModel && isDiscussionRunning && !isPaused,
        linesUp: 1,
    });
    // Phase progress spinner (green) - shows when no model is actively thinking
    useTerminalSpinner({
        text: phaseProgressText,
        color: "green",
        active: isDiscussionRunning && !isPaused && !thinkingModel,
        linesUp: 1,
    });
    // Should we show spinner placeholder?
    const showSpinner = isDiscussionRunning && !isPaused;
    // Explicit cleanup when discussion ends - clears any residual spinner text
    // and refreshes terminal for clean Input rendering
    useEffect(() => {
        if (!isDiscussionRunning) {
            // Show cursor
            process.stdout.write('\x1b[?25h');
            // Clear from cursor to end of screen - lets React re-render cleanly
            process.stdout.write('\x1b[J');
        }
    }, [isDiscussionRunning]);
    return (_jsxs(Box, { flexDirection: "column", paddingX: 1, children: [_jsx(Box, { marginBottom: 1, borderStyle: "single", borderColor: "green", paddingX: 2, children: _jsx(Text, { bold: true, color: "green", children: t("msg.question", { question: currentQuestion || "" }) }) }), _jsx(Box, { flexDirection: "column", children: messages.map((message, index) => (_jsx(Message, { message: message }, `msg-${index}`))) }), completedThinking.length > 0 && isDiscussionRunning && !isPaused && (_jsx(Box, { flexDirection: "column", marginTop: 1, children: completedThinking.map((modelId) => {
                    const displayName = getModelDisplayName(modelId, availableModels);
                    return (_jsxs(Box, { borderStyle: "round", borderColor: "green", paddingX: 1, marginBottom: 0, children: [_jsx(Text, { color: "green", children: "\u2713" }), _jsxs(Text, { children: [" ", t("thinkingComplete", { model: displayName })] })] }, modelId));
                }) })), isPaused && (_jsx(Box, { marginTop: 1, children: _jsx(Box, { borderStyle: "round", borderColor: "cyan", paddingX: 2, paddingY: 0, children: _jsxs(Text, { color: "cyan", bold: true, children: ["\u23F8  ", t("msg.pausePrompt", { previousPhase: previousPhaseName, nextPhase: nextPhaseName })] }) }) })), showSpinner && (_jsx(Text, { children: " " })), isDiscussionComplete && (_jsx(Box, { marginTop: 1, flexDirection: "column", children: _jsxs(Box, { borderStyle: "double", borderColor: "green", paddingX: 2, paddingY: 1, flexDirection: "column", children: [_jsxs(Text, { color: "green", bold: true, children: ["\u2713 ", t("msg.discussionComplete")] }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("msg.pressEscNewDiscussion") }) })] }) }))] }));
}
