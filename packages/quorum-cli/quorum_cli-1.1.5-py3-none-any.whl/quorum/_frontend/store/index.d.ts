/**
 * Zustand store for Quorum frontend state.
 *
 * Uses Immer middleware for O(1) immutable state updates.
 * Instead of spreading objects, we mutate a draft directly.
 */
import type { ModelInfo } from "../ipc/protocol.js";
import type { ConfidenceLevel } from "../types/protocol-values.js";
import type { SupportedLanguage } from "../i18n/index.js";
/**
 * Maximum number of messages to keep in memory.
 * Older messages are trimmed to prevent unbounded memory growth.
 * 500 messages is roughly 50-100 discussions worth of context.
 */
export declare const MAX_MESSAGES = 500;
export type ViewMode = "input" | "discussion";
export type DiscussionMethod = "standard" | "oxford" | "advocate" | "socratic" | "delphi" | "brainstorm" | "tradeoff";
export interface DiscussionMessage {
    type: "phase" | "answer" | "critique" | "chat" | "position" | "synthesis" | "round_header" | "discussion_header";
    phase?: number;
    phaseMessageKey?: string;
    phaseParams?: Record<string, string>;
    source?: string;
    content?: string;
    agreements?: string;
    disagreements?: string;
    missing?: string;
    position?: string;
    confidence?: ConfidenceLevel;
    consensus?: string;
    synthesis?: string;
    differences?: string;
    synthesizerModel?: string;
    confidenceBreakdown?: Record<string, number>;
    role?: "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR" | null;
    roundType?: "opening" | "rebuttal" | "closing" | null;
    method?: DiscussionMethod;
    headerMethod?: DiscussionMethod;
    headerModels?: string[];
    headerRoleAssignments?: Record<string, string[]>;
}
interface StoreState {
    viewMode: ViewMode;
    availableModels: Record<string, ModelInfo[]>;
    selectedModels: string[];
    validatedModels: Set<string>;
    invalidModels: Record<string, string>;
    modelsValidating: boolean;
    validationProgress: {
        current: number;
        total: number;
        sequence: number;
    } | null;
    discussionMethod: DiscussionMethod;
    synthesizerMode: "first" | "random" | "rotate";
    maxTurns: number | null;
    currentDiscussionId: string | null;
    isDiscussionRunning: boolean;
    isDiscussionComplete: boolean;
    currentPhase: number;
    previousPhase: number;
    nextPhase: number;
    currentMethod: DiscussionMethod;
    totalPhases: number;
    messages: DiscussionMessage[];
    isPaused: boolean;
    thinkingModel: string | null;
    currentQuestion: string;
    completedThinking: string[];
    inputValue: string;
    inputHistory: string[];
    historyIndex: number;
    backendReady: boolean;
    backendError: string | null;
    resumeBackend: (() => Promise<void>) | null;
    responseLanguage: SupportedLanguage;
    showModels: boolean;
    showMethods: boolean;
    showHelp: boolean;
    showSynthesizer: boolean;
    showStatus: boolean;
    showTeamPreview: boolean;
    showExportSelector: boolean;
    showAdvisor: boolean;
    showLanguageSelector: boolean;
    setViewMode: (mode: ViewMode) => void;
    setAvailableModels: (models: Record<string, ModelInfo[]>) => void;
    setSelectedModels: (models: string[]) => void;
    addSelectedModel: (modelId: string) => void;
    removeSelectedModel: (modelId: string) => void;
    toggleSelectedModel: (modelId: string) => void;
    setModelsValidating: (validating: boolean) => void;
    setValidationProgress: (progress: {
        current: number;
        total: number;
        sequence: number;
    } | null) => void;
    markModelValidated: (modelId: string) => void;
    markModelInvalid: (modelId: string, error: string) => void;
    setDiscussionMethod: (method: DiscussionMethod) => void;
    setSynthesizerMode: (mode: "first" | "random" | "rotate") => void;
    setMaxTurns: (turns: number | null) => void;
    setInputValue: (value: string) => void;
    setInputHistory: (history: string[]) => void;
    navigateHistory: (direction: "up" | "down") => void;
    addToHistory: (input: string) => void;
    setCurrentDiscussionId: (id: string | null) => void;
    startDiscussion: (question: string) => void;
    addMessage: (message: DiscussionMessage) => void;
    setCurrentPhase: (phase: number) => void;
    setCurrentMethod: (method: DiscussionMethod) => void;
    setTotalPhases: (total: number) => void;
    setPhaseTransition: (completed: number, next: number) => void;
    pauseDiscussion: () => void;
    resumeDiscussion: () => void;
    setThinkingModel: (model: string | null) => void;
    addCompletedThinking: (model: string) => void;
    clearCompletedThinking: () => void;
    completeDiscussion: () => void;
    resetDiscussionState: () => void;
    setBackendReady: (ready: boolean) => void;
    setBackendError: (error: string | null) => void;
    setResumeBackend: (fn: (() => Promise<void>) | null) => void;
    clearMessages: () => void;
    reset: () => void;
    setResponseLanguage: (lang: SupportedLanguage) => void;
    setShowModels: (show: boolean) => void;
    setShowMethods: (show: boolean) => void;
    setShowHelp: (show: boolean) => void;
    setShowSynthesizer: (show: boolean) => void;
    setShowStatus: (show: boolean) => void;
    setShowTeamPreview: (show: boolean) => void;
    setShowExportSelector: (show: boolean) => void;
    setShowAdvisor: (show: boolean) => void;
    setShowLanguageSelector: (show: boolean) => void;
    softReload: () => void;
}
export declare const useStore: import("zustand").UseBoundStore<Omit<import("zustand").StoreApi<StoreState>, "setState"> & {
    setState(nextStateOrUpdater: StoreState | Partial<StoreState> | ((state: import("immer").WritableDraft<StoreState>) => void), shouldReplace?: false): void;
    setState(nextStateOrUpdater: StoreState | ((state: import("immer").WritableDraft<StoreState>) => void), shouldReplace: true): void;
}>;
export {};
