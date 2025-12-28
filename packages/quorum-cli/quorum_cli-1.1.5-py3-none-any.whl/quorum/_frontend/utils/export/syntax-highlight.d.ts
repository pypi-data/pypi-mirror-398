/**
 * Syntax highlighting for PDF code blocks using highlight.js.
 * Converts code to colored tokens for rendering in PDFKit.
 */
/** A token with text and color for PDF rendering */
export interface HighlightToken {
    text: string;
    color: string;
}
/**
 * VS Code Dark+ inspired color palette.
 * Maps highlight.js CSS classes to hex colors.
 */
declare const TOKEN_COLORS: Record<string, string>;
/**
 * Highlight code and return colored tokens for PDF rendering.
 *
 * @param code - The source code to highlight
 * @param language - Optional language hint (e.g., "python", "typescript")
 * @returns Array of tokens with text and color
 */
export declare function highlightCode(code: string, language?: string): HighlightToken[];
/** Dark background color for code blocks (VS Code Dark+) */
export declare const CODE_BACKGROUND = "#1e1e1e";
/** Export color palette for potential customization */
export { TOKEN_COLORS };
