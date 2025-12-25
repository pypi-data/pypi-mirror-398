import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";
const VERSION = "1.1.4";
export function Header() {
    const { selectedModels, discussionMethod, availableModels } = useStore();
    // Get display names for selected models
    const getModelName = (modelId) => {
        for (const models of Object.values(availableModels)) {
            const model = models.find((m) => m.id === modelId);
            if (model?.display_name)
                return model.display_name;
        }
        // Fallback: extract readable name from ID
        return modelId.split("/").pop()?.split(":")[0] || modelId;
    };
    const modelNames = selectedModels.map(getModelName);
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "green", paddingX: 2, paddingY: 0, children: [_jsxs(Box, { justifyContent: "space-between", children: [_jsxs(Box, { children: [_jsx(Text, { bold: true, color: "green", children: t("app.title") }), _jsxs(Text, { dimColor: true, children: [" v", VERSION] })] }), _jsx(Text, { dimColor: true, children: t("app.subtitle") })] }), _jsx(Box, { marginY: 0, children: _jsx(Text, { dimColor: true, children: "─".repeat(70) }) }), _jsxs(Box, { children: [_jsxs(Box, { flexDirection: "column", width: "50%", children: [_jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: t("status.models") }), modelNames.length > 0 ? (_jsx(Text, { children: modelNames.join(", ") })) : (_jsx(Text, { dimColor: true, italic: true, children: t("status.none") }))] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: t("status.method") }), _jsx(Text, { color: "magenta", children: discussionMethod })] })] }), _jsxs(Box, { flexDirection: "column", width: "50%", children: [_jsx(Text, { dimColor: true, bold: true, children: t("header.quickCommands") }), _jsx(Text, { dimColor: true, children: t("header.cmdModels") }), _jsx(Text, { dimColor: true, children: t("header.cmdMethod") }), _jsx(Text, { dimColor: true, children: t("header.cmdExport") }), _jsx(Text, { dimColor: true, children: t("header.cmdHelp") })] })] })] }));
}
