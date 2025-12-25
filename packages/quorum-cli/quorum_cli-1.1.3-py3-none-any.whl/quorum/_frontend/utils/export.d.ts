/**
 * Export discussion to various formats.
 */
import type { DiscussionMessage, DiscussionMethod } from "../store/index.js";
import { type ConfidenceLevel, type RoleValue, type StandardConsensus } from "../types/protocol-values.js";
export type ExportFormat = "md" | "text" | "pdf" | "json";
interface ExportOptions {
    question: string;
    messages: DiscussionMessage[];
    method: DiscussionMethod;
    models: string[];
}
/**
 * Translate role label for export.
 * Uses centralized ROLE_KEYS mapping from protocol-values.ts.
 */
export declare function translateRole(role: string | RoleValue): string;
/**
 * Translate consensus value for export.
 * Uses centralized CONSENSUS_KEYS mapping from protocol-values.ts.
 */
export declare function translateConsensus(value: string | StandardConsensus): string;
/**
 * Translate confidence level for export.
 * Uses centralized CONFIDENCE_KEYS mapping from protocol-values.ts.
 */
export declare function translateConfidence(level: string | ConfidenceLevel | undefined): string;
/**
 * Format a discussion as markdown.
 */
export declare function formatDiscussionAsMarkdown(options: ExportOptions): string;
/**
 * Save discussion to a specific directory (for auto-logging, always markdown).
 * Creates directory if it doesn't exist.
 * Returns the path to the saved file.
 *
 * Security: Validates path just-in-time before write to prevent TOCTOU attacks.
 */
export declare function saveDiscussionToDir(options: ExportOptions, dir: string): Promise<string>;
/**
 * Information about a report file for the export selector.
 */
export interface ReportFileInfo {
    path: string;
    filename: string;
    mtime: Date;
    question: string;
    method: string;
}
/**
 * List recent report files from a directory.
 * Returns the most recent files sorted by modification time.
 */
export declare function listRecentReports(dir: string, limit?: number): Promise<ReportFileInfo[]>;
/**
 * Export a specific log file to a different format.
 * Reads the markdown log and converts to the target format.
 * Returns the path to the exported file.
 *
 * Security: Validates paths just-in-time before write to prevent TOCTOU attacks.
 */
export declare function exportSpecificLog(logPath: string, format: ExportFormat, exportDir: string): Promise<string>;
export {};
