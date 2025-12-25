import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { getModelDisplayName } from "./Message.js";
import { t } from "../i18n/index.js";
export function Status() {
    const { selectedModels, availableModels, discussionMethod, synthesizerMode, maxTurns, setShowStatus, } = useStore();
    useInput((input, key) => {
        if (key.escape) {
            setShowStatus(false);
        }
    });
    const modelNames = selectedModels.map((id) => getModelDisplayName(id, availableModels));
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "blue", paddingX: 2, paddingY: 1, children: [_jsx(Text, { bold: true, color: "blue", children: t("status.title") }), _jsxs(Box, { marginTop: 1, flexDirection: "column", children: [_jsxs(Box, { children: [_jsx(Text, { bold: true, children: t("status.models") }), modelNames.length > 0 ? (_jsx(Text, { color: "green", children: modelNames.join(", ") })) : (_jsx(Text, { dimColor: true, children: t("status.none") }))] }), _jsxs(Box, { children: [_jsx(Text, { bold: true, children: t("status.method") }), _jsx(Text, { color: "cyan", children: discussionMethod })] }), _jsxs(Box, { children: [_jsx(Text, { bold: true, children: t("status.synthesizer") }), _jsx(Text, { children: synthesizerMode })] }), _jsxs(Box, { children: [_jsx(Text, { bold: true, children: t("status.maxTurns") }), _jsx(Text, { children: maxTurns || t("status.default") })] })] })] }));
}
