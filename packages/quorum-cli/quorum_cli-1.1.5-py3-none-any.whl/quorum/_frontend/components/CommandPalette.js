import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Floating command palette component.
 * Appears above the input when "/" is typed.
 */
import { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { t } from "../i18n/index.js";
// Commands with translated descriptions
const getCommands = () => [
    { name: "/models", description: t("cmd.models"), shortcut: "m" },
    { name: "/method", description: t("cmd.method") },
    { name: "/synthesizer", description: t("cmd.synthesizer") },
    { name: "/language", description: t("cmd.language") },
    { name: "/status", description: t("cmd.status"), shortcut: "s" },
    { name: "/export", description: t("cmd.export"), hasParams: true },
    { name: "/clear", description: t("cmd.clear"), shortcut: "c" },
    { name: "/help", description: t("cmd.help"), shortcut: "?" },
    { name: "/quit", description: t("cmd.quit"), shortcut: "q" },
    { name: "/maxturns", description: t("cmd.turns"), hasParams: true },
];
export function CommandPalette({ filter, onSelect, onClose }) {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const COMMANDS = getCommands();
    // Filter commands
    const filteredCommands = filter
        ? COMMANDS.filter((cmd) => cmd.name.toLowerCase().includes(filter.toLowerCase()))
        : COMMANDS;
    // Reset selection when filter changes
    useEffect(() => {
        setSelectedIndex(0);
    }, [filter]);
    // Handle keyboard navigation
    useInput((input, key) => {
        if (key.escape) {
            onClose();
            return;
        }
        if (key.upArrow) {
            setSelectedIndex((prev) => Math.max(0, prev - 1));
            return;
        }
        if (key.downArrow) {
            setSelectedIndex((prev) => Math.min(filteredCommands.length - 1, prev + 1));
            return;
        }
        if (key.return) {
            if (filteredCommands.length > 0) {
                const cmd = filteredCommands[selectedIndex];
                onSelect(cmd.name, !cmd.hasParams);
            }
            else {
                // No matches - close palette, let Input handle the command
                onClose();
            }
            return;
        }
        if (key.tab && filteredCommands.length > 0) {
            const cmd = filteredCommands[selectedIndex];
            // Tab always just fills in the command, doesn't execute
            onSelect(cmd.name, false);
            return;
        }
    });
    if (filteredCommands.length === 0) {
        return (_jsx(Box, { flexDirection: "column", borderStyle: "round", borderColor: "gray", paddingX: 1, children: _jsx(Text, { dimColor: true, children: t("palette.noMatches") }) }));
    }
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "green", paddingX: 1, children: [_jsxs(Box, { marginBottom: 0, children: [_jsx(Text, { bold: true, color: "green", children: t("palette.title") }), _jsxs(Text, { dimColor: true, children: [" ", t("palette.hint")] })] }), filteredCommands.map((cmd, index) => {
                const isSelected = index === selectedIndex;
                return (_jsxs(Box, { children: [_jsx(Text, { backgroundColor: isSelected ? "green" : undefined, color: isSelected ? "black" : "cyan", bold: isSelected, children: cmd.name.padEnd(12) }), _jsxs(Text, { dimColor: !isSelected, children: [" ", cmd.description] }), cmd.shortcut && (_jsxs(Text, { dimColor: true, children: [" [", cmd.shortcut, "]"] }))] }, cmd.name));
            })] }));
}
