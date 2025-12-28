import { jsxs as _jsxs, jsx as _jsx, Fragment as _Fragment } from "react/jsx-runtime";
/**
 * Method Advisor - AI-powered method recommendation panel.
 * Triggered by Tab key, analyzes a question and recommends the best discussion method.
 */
import { useState, useEffect, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { t } from "../i18n/index.js";
import { SPINNER_FRAMES, SPINNER_INTERVAL_MS } from "../hooks/useSpinner.js";
// Method display info
const METHOD_INFO = {
    standard: { name: "Standard", color: "white" },
    oxford: { name: "Oxford Debate", color: "yellow" },
    advocate: { name: "Devil's Advocate", color: "red" },
    socratic: { name: "Socratic", color: "cyan" },
    delphi: { name: "Delphi", color: "magenta" },
    brainstorm: { name: "Brainstorm", color: "green" },
    tradeoff: { name: "Tradeoff", color: "blue" },
};
// Spinner component
function Spinner({ text }) {
    const [frame, setFrame] = useState(0);
    useEffect(() => {
        const timer = setInterval(() => {
            setFrame((f) => (f + 1) % SPINNER_FRAMES.length);
        }, SPINNER_INTERVAL_MS);
        return () => clearInterval(timer);
    }, []);
    return (_jsxs(Text, { color: "cyan", children: [SPINNER_FRAMES[frame], " ", text] }));
}
export function MethodAdvisor({ onSelect, onCancel, analyzeQuestion }) {
    const [phase, setPhase] = useState("input");
    const [question, setQuestion] = useState("");
    const [cursorPosition, setCursorPosition] = useState(0);
    const [advisorModel, setAdvisorModel] = useState(null);
    const [recommendations, setRecommendations] = useState(null);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [error, setError] = useState(null);
    // Get all recommendations as a flat list for navigation
    const allRecommendations = recommendations
        ? [recommendations.primary, ...recommendations.alternatives]
        : [];
    const handleAnalyze = useCallback(async () => {
        if (!question.trim())
            return;
        setPhase("analyzing");
        setError(null);
        try {
            const result = await analyzeQuestion(question);
            setAdvisorModel(result.advisor_model);
            setRecommendations(result.recommendations);
            setPhase("results");
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Analysis failed");
            setPhase("input");
        }
    }, [question, analyzeQuestion]);
    useInput((input, key) => {
        if (key.escape) {
            onCancel();
            return;
        }
        if (phase === "input") {
            // Handle Enter to analyze
            if (key.return && question.trim()) {
                handleAnalyze();
                return;
            }
            // Handle Backspace
            if (key.backspace || key.delete) {
                if (cursorPosition > 0) {
                    const newValue = question.slice(0, cursorPosition - 1) + question.slice(cursorPosition);
                    setQuestion(newValue);
                    setCursorPosition(cursorPosition - 1);
                }
                return;
            }
            // Handle arrow keys for cursor
            if (key.leftArrow) {
                setCursorPosition(Math.max(0, cursorPosition - 1));
                return;
            }
            if (key.rightArrow) {
                setCursorPosition(Math.min(question.length, cursorPosition + 1));
                return;
            }
            // Handle regular character input
            if (input && !key.ctrl && !key.meta && !key.tab) {
                const newValue = question.slice(0, cursorPosition) + input + question.slice(cursorPosition);
                setQuestion(newValue);
                setCursorPosition(cursorPosition + input.length);
            }
        }
        else if (phase === "results") {
            // Navigate recommendations
            if (key.upArrow) {
                setSelectedIndex(Math.max(0, selectedIndex - 1));
                return;
            }
            if (key.downArrow) {
                setSelectedIndex(Math.min(allRecommendations.length - 1, selectedIndex + 1));
                return;
            }
            // Select recommendation
            if (key.return) {
                const selected = allRecommendations[selectedIndex];
                if (selected) {
                    onSelect(selected.method, question);
                }
                return;
            }
            // Go back to input
            if (key.backspace) {
                setPhase("input");
                setRecommendations(null);
                setSelectedIndex(0);
                return;
            }
        }
    });
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "cyan", paddingX: 2, paddingY: 1, children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, color: "cyan", children: t("advisor.title") }) }), phase === "input" && (_jsxs(_Fragment, { children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { dimColor: true, children: t("advisor.prompt") }) }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", bold: true, children: "› " }), question ? (_jsxs(_Fragment, { children: [_jsx(Text, { children: question.slice(0, cursorPosition) }), _jsx(Text, { backgroundColor: "white", color: "black", children: question[cursorPosition] || " " }), _jsx(Text, { children: question.slice(cursorPosition + 1) })] })) : (_jsx(Text, { backgroundColor: "white", color: "black", children: " " }))] }), error && (_jsx(Box, { marginTop: 1, children: _jsxs(Text, { color: "red", children: [t("advisor.error"), ": ", error] }) })), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("advisor.inputHint") }) })] })), phase === "analyzing" && (_jsx(Box, { children: _jsx(Spinner, { text: t("advisor.analyzing", { model: advisorModel || "AI" }) }) })), phase === "results" && recommendations && (_jsxs(_Fragment, { children: [_jsx(Box, { marginBottom: 1, children: _jsxs(Text, { dimColor: true, children: ["\"", question, "\""] }) }), _jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, children: t("advisor.recommended") }) }), allRecommendations.map((rec, index) => {
                        const info = METHOD_INFO[rec.method] || { name: rec.method, color: "white" };
                        const isSelected = index === selectedIndex;
                        const isPrimary = index === 0;
                        return (_jsxs(Box, { flexDirection: "column", marginBottom: isPrimary ? 1 : 0, children: [_jsx(Box, { children: _jsxs(Text, { backgroundColor: isSelected ? "cyan" : undefined, color: isSelected ? "black" : info.color, bold: isPrimary, children: [isPrimary ? "● " : "○ ", info.name, " (", rec.confidence, "%)"] }) }), (isPrimary || isSelected) && (_jsx(Box, { marginLeft: 2, children: _jsx(Text, { dimColor: true, wrap: "wrap", children: rec.reason }) }))] }, rec.method));
                    }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("advisor.navigation") }) }), advisorModel && (_jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, italic: true, children: t("advisor.analyzedBy", { model: advisorModel }) }) }))] }))] }));
}
