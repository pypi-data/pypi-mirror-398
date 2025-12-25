import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Terminal markdown renderer using ink components.
 */
import React from "react";
import { Text, Box } from "ink";
import { parseMarkdown } from "./markdown.js";
// =============================================================================
// Inline Token Renderer
// =============================================================================
function renderToken(token, key) {
    switch (token.type) {
        case "bold":
            return _jsx(Text, { bold: true, children: token.content }, key);
        case "italic":
            return _jsx(Text, { italic: true, children: token.content }, key);
        case "code":
            return _jsx(Text, { color: "cyan", children: token.content }, key);
        case "link":
            // Show link text with URL in parentheses
            return _jsx(Text, { color: "blue", children: token.content }, key);
        case "math":
            // Math tokens have Unicode-converted content for terminal display
            return _jsx(Text, { children: token.content }, key);
        case "text":
        default:
            return _jsx(Text, { children: token.content }, key);
    }
}
function renderTokens(tokens) {
    return tokens.map((token, i) => renderToken(token, i));
}
// =============================================================================
// Table Renderer
// =============================================================================
/**
 * Get plain text content from tokens for measuring width.
 */
function getTokensText(tokens) {
    return tokens.map((t) => t.content).join("");
}
/**
 * Render a properly formatted table with box-drawing characters.
 */
function renderTable(rows, key) {
    if (rows.length === 0)
        return null;
    // Calculate column widths (max width per column, min 3 chars)
    const numCols = Math.max(...rows.map((r) => r.cells.length));
    const colWidths = Array(numCols).fill(3);
    for (const row of rows) {
        for (let i = 0; i < row.cells.length; i++) {
            const text = getTokensText(row.cells[i]);
            colWidths[i] = Math.max(colWidths[i], text.length);
        }
    }
    // Build horizontal lines
    const topLine = "┌" + colWidths.map((w) => "─".repeat(w + 2)).join("┬") + "┐";
    const sepLine = "├" + colWidths.map((w) => "─".repeat(w + 2)).join("┼") + "┤";
    const botLine = "└" + colWidths.map((w) => "─".repeat(w + 2)).join("┴") + "┘";
    // Render a row with proper padding, preserving inline formatting
    const renderRow = (row, rowIndex) => {
        const cells = colWidths.map((width, i) => {
            const cellTokens = row.cells[i] || [];
            const text = getTokensText(cellTokens);
            const padding = " ".repeat(Math.max(0, width - text.length));
            // Render tokens with formatting, add padding at end
            return (_jsxs(Text, { bold: row.isHeader, children: [" ", renderTokens(cellTokens), padding, " "] }, i));
        });
        return (_jsxs(Box, { children: [_jsx(Text, { dimColor: true, children: "\u2502" }), cells.map((cell, i) => (_jsxs(React.Fragment, { children: [cell, _jsx(Text, { dimColor: true, children: "\u2502" })] }, i)))] }, `row-${rowIndex}`));
    };
    // Build the table
    const elements = [];
    elements.push(_jsx(Text, { dimColor: true, children: topLine }, "top"));
    for (let i = 0; i < rows.length; i++) {
        elements.push(renderRow(rows[i], i));
        // Add separator after header row
        if (rows[i].isHeader && i < rows.length - 1) {
            elements.push(_jsx(Text, { dimColor: true, children: sepLine }, "sep"));
        }
    }
    elements.push(_jsx(Text, { dimColor: true, children: botLine }, "bot"));
    return (_jsx(Box, { flexDirection: "column", marginY: 1, children: elements }, key));
}
// =============================================================================
// Line Renderer
// =============================================================================
function renderLine(line, key) {
    switch (line.type) {
        case "empty":
            return _jsx(Text, { children: " " }, key);
        case "hr":
            return (_jsx(Box, { marginY: 1, children: _jsx(Text, { dimColor: true, children: "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500" }) }, key));
        case "header":
            // Different colors for header levels (1-6)
            const headerColor = line.level === 1 ? "green"
                : line.level === 2 ? "yellow"
                    : line.level === 3 ? "cyan"
                        : "white";
            return (_jsx(Box, { marginTop: line.level === 1 ? 1 : 0, children: _jsx(Text, { bold: true, color: headerColor, children: renderTokens(line.tokens) }) }, key));
        case "blockquote":
            return (_jsxs(Box, { marginLeft: 2, children: [_jsx(Text, { color: "gray", children: "\u2502 " }), _jsx(Text, { italic: true, children: renderTokens(line.tokens) })] }, key));
        case "bullet":
            return (_jsxs(Box, { marginLeft: 2, children: [_jsx(Text, { children: "\u2022 " }), _jsx(Text, { children: renderTokens(line.tokens) })] }, key));
        case "numbered":
            return (_jsxs(Box, { marginLeft: 2, children: [_jsxs(Text, { children: [line.number, ". "] }), _jsx(Text, { children: renderTokens(line.tokens) })] }, key));
        case "code-block":
            return (_jsxs(Box, { flexDirection: "column", marginY: 1, paddingX: 1, borderStyle: "single", borderColor: "gray", children: [line.language && (_jsx(Text, { dimColor: true, children: line.language })), _jsx(Text, { color: "cyan", children: line.code })] }, key));
        case "table":
            return renderTable(line.tableRows || [], key);
        case "paragraph":
        default:
            return (_jsx(Text, { children: renderTokens(line.tokens) }, key));
    }
}
export function Markdown({ children }) {
    const lines = parseMarkdown(children);
    return (_jsx(Box, { flexDirection: "column", children: lines.map((line, i) => renderLine(line, i)) }));
}
