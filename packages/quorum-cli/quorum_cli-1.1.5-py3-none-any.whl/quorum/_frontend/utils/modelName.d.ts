/**
 * Shared model name formatting utilities.
 * Consolidates duplicate formatting logic from Message.tsx and export.ts.
 */
import type { ModelInfo } from "../ipc/protocol.js";
/**
 * Format a model ID into a readable display name.
 * Converts "grok-4-1-fast-reasoning" to "Grok 4.1 Fast Reasoning"
 * Idempotent: already formatted names pass through unchanged.
 * Results are memoized for performance.
 */
export declare function formatModelName(modelId: string): string;
/**
 * Look up display name for a model ID from available models.
 * Falls back to formatted model name if not found in the models registry.
 */
export declare function getModelDisplayName(modelId: string, availableModels: Record<string, ModelInfo[]>): string;
