/**
 * Shared spinner hook for terminal-based spinners.
 * Consolidates duplicate spinner logic from Discussion.tsx and MethodAdvisor.tsx.
 */
/** Spinner animation frames */
export declare const SPINNER_FRAMES: string[];
/** Animation interval in milliseconds */
export declare const SPINNER_INTERVAL_MS = 80;
export interface UseTerminalSpinnerOptions {
    /** Text to display next to the spinner */
    text: string;
    /** Spinner color */
    color: "yellow" | "green";
    /** Whether the spinner is active */
    active: boolean;
    /** Number of lines to move up from cursor (default: 1) */
    linesUp?: number;
}
/**
 * Terminal spinner hook that writes directly to stdout with cursor positioning.
 * Used for smooth spinner animations without React re-renders.
 */
export declare function useTerminalSpinner({ text, color, active, linesUp, }: UseTerminalSpinnerOptions): void;
/**
 * Simple in-place spinner hook for inline animations (like MethodAdvisor).
 * Returns the current spinner frame as a string.
 */
export declare function useInlineSpinner(active: boolean): string;
