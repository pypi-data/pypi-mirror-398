import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Export selector for choosing which discussion to export.
 * Shows the 10 most recent discussions with navigation.
 */
import { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { listRecentReports } from "../utils/export.js";
import { t } from "../i18n/index.js";
/**
 * Format a date for display.
 */
function formatDate(date) {
    return date.toLocaleString("sv-SE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}
export function ExportSelector({ reportDir, format, onExport, onCancel }) {
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    // Load report files asynchronously
    useEffect(() => {
        let mounted = true;
        async function loadReports() {
            try {
                const loadedReports = await listRecentReports(reportDir, 10);
                if (mounted) {
                    setReports(loadedReports);
                    setLoading(false);
                }
            }
            catch {
                if (mounted) {
                    setReports([]);
                    setLoading(false);
                }
            }
        }
        loadReports();
        return () => { mounted = false; };
    }, [reportDir]);
    useInput((input, key) => {
        if (key.escape) {
            onCancel();
            return;
        }
        if (loading)
            return;
        if (key.upArrow) {
            setSelectedIndex(prev => Math.max(0, prev - 1));
            return;
        }
        if (key.downArrow) {
            setSelectedIndex(prev => Math.min(reports.length - 1, prev + 1));
            return;
        }
        if (key.return && reports.length > 0) {
            onExport(reports[selectedIndex].path);
            return;
        }
    });
    // Loading state
    if (loading) {
        return (_jsx(Box, { flexDirection: "column", borderStyle: "round", borderColor: "blue", paddingX: 2, paddingY: 1, children: _jsx(Text, { color: "blue", bold: true, children: t("export.loading") }) }));
    }
    // No reports found
    if (reports.length === 0) {
        return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "yellow", paddingX: 2, paddingY: 1, children: [_jsx(Text, { color: "yellow", bold: true, children: t("export.noDiscussions") }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("export.noDiscussionsDir", { dir: reportDir }) }) }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("export.close") }) })] }));
    }
    return (_jsxs(Box, { flexDirection: "column", borderStyle: "round", borderColor: "blue", paddingX: 2, paddingY: 1, children: [_jsx(Box, { marginBottom: 1, children: _jsx(Text, { bold: true, color: "blue", children: t("export.title", { format: format.toUpperCase() }) }) }), _jsx(Box, { marginBottom: 1, children: _jsx(Text, { dimColor: true, children: t("export.selectPrompt") }) }), reports.map((log, index) => {
                const isCursor = index === selectedIndex;
                const methodLabel = log.method.toUpperCase();
                return (_jsxs(Box, { flexDirection: "column", children: [_jsx(Box, { children: _jsxs(Text, { backgroundColor: isCursor ? "blue" : undefined, color: isCursor ? "white" : undefined, bold: isCursor, children: [isCursor ? " > " : "   ", index + 1, ". ", log.question, log.question.length >= 60 ? "..." : ""] }) }), _jsxs(Box, { marginLeft: 5, children: [_jsxs(Text, { color: isCursor ? "cyan" : "yellow", bold: true, children: ["[", methodLabel, "]"] }), _jsx(Text, { children: " " }), _jsx(Text, { color: isCursor ? "blue" : "gray", dimColor: !isCursor, children: formatDate(log.mtime) })] })] }, log.path));
            }), _jsx(Box, { marginTop: 1, children: _jsx(Text, { dimColor: true, children: t("export.navigation") }) })] }));
}
