/**
 * Parser factory and re-exports.
 * Entry point for method-aware markdown parsing.
 */
import type { BaseExportDocument, DiscussionMethod, ParseResult } from "../schemas/index.js";
import { BaseParser } from "./base-parser.js";
export { BaseParser } from "./base-parser.js";
export { StandardParser } from "./standard-parser.js";
export { OxfordParser } from "./oxford-parser.js";
export { AdvocateParser } from "./advocate-parser.js";
export { SocraticParser } from "./socratic-parser.js";
export { DelphiParser } from "./delphi-parser.js";
export { BrainstormParser } from "./brainstorm-parser.js";
export { TradeoffParser } from "./tradeoff-parser.js";
export { ParserValidationError, detectMethod } from "./types.js";
export type { ParsedRole } from "./types.js";
export type { ParseResult } from "../schemas/index.js";
export * from "../schemas/index.js";
/**
 * Creates a method-specific parser based on the markdown content.
 * Automatically detects the discussion method from the markdown.
 *
 * @param markdown - The markdown content to parse
 * @returns A parser instance appropriate for the detected method
 *
 * @example
 * ```typescript
 * const parser = createParser(markdownContent);
 * const { document, warnings } = parser.parse();
 * console.log(document.metadata.method); // e.g., "oxford"
 * ```
 */
export declare function createParser(markdown: string): BaseParser<BaseExportDocument>;
/**
 * Creates a parser for a specific method.
 * Use this when you know the method in advance.
 *
 * @param markdown - The markdown content to parse
 * @param method - The discussion method to use
 * @returns A parser instance for the specified method
 *
 * @example
 * ```typescript
 * const parser = createParserForMethod(markdownContent, "oxford");
 * const { document, warnings } = parser.parse();
 * ```
 */
export declare function createParserForMethod(markdown: string, method: DiscussionMethod): BaseParser<BaseExportDocument>;
/**
 * Parses a markdown discussion log and returns a structured document.
 * This is the main entry point for parsing.
 *
 * @param markdown - The markdown content to parse
 * @returns Parse result with document and any warnings
 *
 * @example
 * ```typescript
 * const { document, warnings } = parseMarkdownLog(markdownContent);
 *
 * if (warnings.length > 0) {
 *   console.warn("Parse warnings:", warnings);
 * }
 *
 * // Access method-specific data
 * if (document.metadata.method === "oxford") {
 *   const oxfordDoc = document as OxfordExportDocument;
 *   console.log("Decision:", oxfordDoc.synthesis.decision);
 * }
 * ```
 */
export declare function parseMarkdownLog(markdown: string): ParseResult<BaseExportDocument>;
/**
 * Parses a markdown log with a specific method parser.
 *
 * @param markdown - The markdown content to parse
 * @param method - The discussion method to use
 * @returns Parse result with document and any warnings
 */
export declare function parseMarkdownLogWithMethod(markdown: string, method: DiscussionMethod): ParseResult<BaseExportDocument>;
/**
 * Gets a list of all supported discussion methods.
 *
 * @returns Array of method names
 */
export declare function getSupportedMethods(): DiscussionMethod[];
/**
 * Checks if a method is supported.
 *
 * @param method - The method name to check
 * @returns True if the method is supported
 */
export declare function isMethodSupported(method: string): method is DiscussionMethod;
