/**
 * Shared markdown parser for terminal and PDF rendering.
 * Supports a minimal subset of markdown for maximum compatibility.
 */
export interface InlineToken {
    type: "text" | "bold" | "italic" | "code" | "link" | "math";
    content: string;
    url?: string;
    raw?: string;
}
export interface TableRow {
    cells: InlineToken[][];
    isHeader: boolean;
}
export interface ParsedLine {
    type: "paragraph" | "header" | "bullet" | "numbered" | "empty" | "hr" | "blockquote" | "code-block" | "table";
    level?: number;
    number?: number;
    tokens: InlineToken[];
    raw: string;
    language?: string;
    code?: string;
    tableRows?: TableRow[];
}
export declare const SUBSCRIPTS: Record<string, string>;
export declare const SUPERSCRIPTS: Record<string, string>;
export declare const LATEX_COMMANDS: Record<string, string>;
/**
 * Parse markdown text into structured lines.
 * Uses two-pass approach for multi-line blocks (code blocks, tables).
 */
export declare function parseMarkdown(text: string): ParsedLine[];
/**
 * Convert tokens to plain text (strips formatting).
 */
export declare function tokensToPlainText(tokens: InlineToken[]): string;
