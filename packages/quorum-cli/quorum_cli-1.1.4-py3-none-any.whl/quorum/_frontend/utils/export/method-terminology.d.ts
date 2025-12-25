/**
 * Method-specific terminology registry for export formatting.
 * Single source of truth for all 7 discussion methods.
 * Uses i18n for translated labels.
 */
import type { DiscussionMethod } from "../../store/index.js";
/**
 * Labels and configuration for a discussion method's export formatting.
 */
export interface MethodTerminology {
    /** Header for result section (e.g., "Result", "Verdict", "Aporia") */
    resultLabel: string;
    /** Header for synthesis content (e.g., "Synthesis", "Ruling", "Reflection") */
    synthesisLabel: string;
    /** Header for differences section (e.g., "Notable Differences", "Open Questions") */
    differencesLabel: string;
    /** Attribution prefix (e.g., "Synthesized by", "Ruled by") */
    byLabel: string;
    /** Label for consensus line (e.g., "Consensus", "Decision", "Convergence") */
    consensusLabel: string;
    /** Whether to show consensus as separate line (false for Advocate) */
    showConsensus: boolean;
    /** Banner color for PDF export */
    bannerColor: string;
}
/**
 * Get terminology for a discussion method.
 * Labels are dynamically translated using the current language.
 * @param method - The discussion method
 * @returns Method-specific terminology
 */
export declare function getMethodTerminology(method: DiscussionMethod): MethodTerminology;
/**
 * Get result label in uppercase (for plain text export).
 */
export declare function getResultLabelUppercase(method: DiscussionMethod): string;
