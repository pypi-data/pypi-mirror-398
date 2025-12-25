import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Box, Text, useInput } from "ink";
import { t } from "../i18n/index.js";
import { useStore } from "../store/index.js";
export function Help() {
    const { setShowHelp } = useStore();
    useInput((input, key) => {
        if (key.escape) {
            setShowHelp(false);
        }
    });
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "yellow", paddingX: 2, paddingY: 1, children: [_jsx(Text, { bold: true, color: "yellow", children: t("help.title") }), _jsxs(Box, { marginTop: 1, flexDirection: "column", children: [_jsx(Text, { bold: true, dimColor: true, children: t("help.commands") }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/models".padEnd(12) }), _jsx(Text, { children: t("cmd.models") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/method".padEnd(12) }), _jsx(Text, { children: t("cmd.method") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/synthesizer".padEnd(12) }), _jsx(Text, { children: t("cmd.synthesizer") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/status".padEnd(12) }), _jsx(Text, { children: t("cmd.status") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/export".padEnd(12) }), _jsx(Text, { children: t("cmd.export") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/clear".padEnd(12) }), _jsx(Text, { children: t("cmd.clear") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "/quit".padEnd(12) }), _jsx(Text, { children: t("cmd.quit") })] })] }), _jsxs(Box, { marginTop: 1, flexDirection: "column", children: [_jsx(Text, { bold: true, dimColor: true, children: t("help.keyboard") }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "Esc".padEnd(12) }), _jsx(Text, { children: t("help.key.esc") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "Ctrl+C".padEnd(12) }), _jsx(Text, { children: t("help.key.ctrlC") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: String.fromCharCode(0x2191) + String.fromCharCode(0x2193).padEnd(10) }), _jsx(Text, { children: t("help.key.arrows") })] }), _jsxs(Box, { children: [_jsx(Text, { color: "cyan", children: "Enter".padEnd(12) }), _jsx(Text, { children: t("help.key.enter") })] })] }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("help.close") }) })] }));
}
