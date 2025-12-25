/**
 * Shared types and patterns for method-aware markdown parsing.
 * IMPORTANT: Patterns MUST match EXACTLY what i18n translations produce.
 */
import type { DiscussionMethod } from "../schemas/index.js";
/**
 * Regex patterns for identifying markdown elements.
 * Multi-language support: patterns match all 6 supported languages (EN, SV, DE, FR, ES, IT)
 */
export declare const STRUCTURAL_PATTERNS: {
    QUESTION: RegExp;
    DISCUSSION: RegExp;
    RESULT: RegExp;
    PHASE: RegExp;
    MESSAGE: RegExp;
    SYNTHESIS_HEADER: RegExp;
    DIFFERENCES_HEADER: RegExp;
    CONSENSUS_LINE: RegExp;
    SYNTHESIZER_LINE: RegExp;
    AGREEMENTS: RegExp;
    DISAGREEMENTS: RegExp;
    MISSING: RegExp;
    CONFIDENCE: RegExp;
    SEPARATOR: RegExp;
    FOOTER: RegExp;
};
export declare const METADATA_PATTERNS: {
    DATE: RegExp;
    METHOD: RegExp;
    MODELS: RegExp;
};
export declare const MESSAGE_TYPE_LABELS: {
    CRITIQUE: string[];
    POSITION: string[];
};
/** Role types across all methods */
export type ParsedRole = "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR" | null;
/** Raw parsed metadata before method-specific processing */
export interface RawMetadata {
    date: string;
    method: string;
    models: string[];
}
/** Validation error for method-specific constraints */
export declare class ParserValidationError extends Error {
    methodName: string;
    message: string;
    phase?: number | undefined;
    details?: Record<string, unknown> | undefined;
    constructor(methodName: string, message: string, phase?: number | undefined, details?: Record<string, unknown> | undefined);
}
/** Method name to DiscussionMethod mapping */
export declare function normalizeMethodName(method: string): DiscussionMethod;
/** Detect method from markdown content */
export declare function detectMethod(markdown: string): DiscussionMethod;
