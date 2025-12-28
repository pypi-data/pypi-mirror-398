/**
 * Zustand store for Quorum frontend state.
 *
 * Uses Immer middleware for O(1) immutable state updates.
 * Instead of spreading objects, we mutate a draft directly.
 */
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { enableMapSet } from "immer";
// Enable Map/Set support in Immer
enableMapSet();
// ============================================================================
// Constants
// ============================================================================
/**
 * Maximum number of messages to keep in memory.
 * Older messages are trimmed to prevent unbounded memory growth.
 * 500 messages is roughly 50-100 discussions worth of context.
 */
export const MAX_MESSAGES = 500;
/** ANSI escape sequence to clear screen, scrollback, and move cursor home */
const CLEAR_SCREEN = "\x1b[2J\x1b[3J\x1b[H";
// ============================================================================
// Initial State
// ============================================================================
const initialState = {
    viewMode: "input",
    availableModels: {},
    selectedModels: [],
    validatedModels: new Set(),
    invalidModels: {},
    modelsValidating: false,
    validationProgress: null,
    discussionMethod: "standard",
    synthesizerMode: "first",
    maxTurns: null,
    currentDiscussionId: null,
    isDiscussionRunning: false,
    isDiscussionComplete: false,
    currentPhase: 0,
    previousPhase: 0,
    nextPhase: 0,
    currentMethod: "standard",
    totalPhases: 5, // Standard has 5 phases
    messages: [],
    isPaused: false,
    thinkingModel: null,
    currentQuestion: "",
    completedThinking: [],
    inputValue: "",
    inputHistory: [],
    historyIndex: -1,
    backendReady: false,
    backendError: null,
    resumeBackend: null,
    // Language
    responseLanguage: "en",
    // UI Modals
    showModels: false,
    showMethods: false,
    showHelp: false,
    showSynthesizer: false,
    showStatus: false,
    showTeamPreview: false,
    showExportSelector: false,
    showAdvisor: false,
    showLanguageSelector: false,
};
// ============================================================================
// Store
// ============================================================================
export const useStore = create()(immer((set) => ({
    ...initialState,
    setViewMode: (mode) => set((state) => { state.viewMode = mode; }),
    setAvailableModels: (models) => set((state) => { state.availableModels = models; }),
    setSelectedModels: (models) => set((state) => { state.selectedModels = models; }),
    addSelectedModel: (modelId) => set((state) => {
        if (!state.selectedModels.includes(modelId)) {
            state.selectedModels.push(modelId);
        }
    }),
    removeSelectedModel: (modelId) => set((state) => {
        const index = state.selectedModels.indexOf(modelId);
        if (index !== -1) {
            state.selectedModels.splice(index, 1);
        }
    }),
    toggleSelectedModel: (modelId) => set((state) => {
        const index = state.selectedModels.indexOf(modelId);
        if (index !== -1) {
            state.selectedModels.splice(index, 1);
        }
        else {
            state.selectedModels.push(modelId);
        }
    }),
    setModelsValidating: (validating) => set((state) => { state.modelsValidating = validating; }),
    setValidationProgress: (progress) => set((state) => {
        // Only update if new sequence is higher or resetting to null
        if (progress === null) {
            state.validationProgress = null;
        }
        else if (state.validationProgress === null ||
            progress.sequence > state.validationProgress.sequence) {
            state.validationProgress = progress;
        }
    }),
    markModelValidated: (modelId) => set((state) => {
        state.validatedModels.add(modelId);
    }),
    markModelInvalid: (modelId, error) => set((state) => {
        state.invalidModels[modelId] = error;
    }),
    setDiscussionMethod: (method) => set((state) => { state.discussionMethod = method; }),
    setSynthesizerMode: (mode) => set((state) => { state.synthesizerMode = mode; }),
    setMaxTurns: (turns) => set((state) => { state.maxTurns = turns; }),
    setInputValue: (value) => set((state) => {
        state.inputValue = value;
        state.historyIndex = -1;
    }),
    setInputHistory: (history) => set((state) => { state.inputHistory = history; }),
    navigateHistory: (direction) => set((state) => {
        const history = state.inputHistory;
        if (history.length === 0)
            return;
        if (direction === "up") {
            if (state.historyIndex < history.length - 1) {
                state.historyIndex++;
            }
        }
        else {
            if (state.historyIndex > -1) {
                state.historyIndex--;
            }
        }
        state.inputValue = state.historyIndex === -1
            ? ""
            : history[history.length - 1 - state.historyIndex];
    }),
    addToHistory: (input) => set((state) => {
        // Remove duplicate if exists
        const existingIndex = state.inputHistory.indexOf(input);
        if (existingIndex !== -1) {
            state.inputHistory.splice(existingIndex, 1);
        }
        // Add to end
        state.inputHistory.push(input);
        // Limit size
        if (state.inputHistory.length > 100) {
            state.inputHistory.splice(0, state.inputHistory.length - 100);
        }
        state.historyIndex = -1;
    }),
    setCurrentDiscussionId: (id) => set((state) => {
        state.currentDiscussionId = id;
    }),
    startDiscussion: (question) => set((state) => {
        state.isDiscussionRunning = true;
        state.currentQuestion = question;
        state.messages = [];
        state.isPaused = false;
        state.thinkingModel = null;
        state.currentPhase = 0;
        state.previousPhase = 0;
        state.nextPhase = 0;
        state.completedThinking = [];
        state.viewMode = "discussion";
        // Note: currentDiscussionId is set by App.tsx when backend confirms discussion start
    }),
    addMessage: (message) => set((state) => {
        // Add new message with windowing to prevent unbounded growth
        state.messages.push(message);
        // Trim oldest messages if we exceed the limit
        if (state.messages.length > MAX_MESSAGES) {
            state.messages.splice(0, state.messages.length - MAX_MESSAGES);
        }
        state.thinkingModel = null;
    }),
    setCurrentPhase: (phase) => set((state) => { state.currentPhase = phase; }),
    setCurrentMethod: (method) => set((state) => { state.currentMethod = method; }),
    setTotalPhases: (total) => set((state) => { state.totalPhases = total; }),
    setPhaseTransition: (completed, next) => set((state) => {
        state.previousPhase = completed;
        state.nextPhase = next;
    }),
    pauseDiscussion: () => set((state) => { state.isPaused = true; }),
    resumeDiscussion: () => set((state) => { state.isPaused = false; }),
    setThinkingModel: (model) => set((state) => { state.thinkingModel = model; }),
    addCompletedThinking: (model) => set((state) => {
        if (!state.completedThinking.includes(model)) {
            state.completedThinking.push(model);
        }
    }),
    clearCompletedThinking: () => set((state) => { state.completedThinking = []; }),
    completeDiscussion: () => set((state) => {
        state.isDiscussionRunning = false;
        state.isDiscussionComplete = true;
        state.isPaused = false;
        state.thinkingModel = null;
    }),
    // Reset discussion state without clearing screen (for error handling)
    resetDiscussionState: () => set((state) => {
        state.isDiscussionRunning = false;
        state.isDiscussionComplete = false;
        state.currentPhase = 0;
        state.currentQuestion = "";
        state.messages = [];
        state.isPaused = false;
        state.thinkingModel = null;
        state.completedThinking = [];
    }),
    setBackendReady: (ready) => set((state) => { state.backendReady = ready; }),
    setBackendError: (error) => set((state) => { state.backendError = error; }),
    setResumeBackend: (fn) => set((state) => { state.resumeBackend = fn; }),
    clearMessages: () => set((state) => {
        state.messages = [];
        state.currentPhase = 0;
        state.previousPhase = 0;
        state.nextPhase = 0;
    }),
    reset: () => set(() => initialState),
    // Language actions
    setResponseLanguage: (lang) => set((state) => { state.responseLanguage = lang; }),
    // Modal actions
    setShowModels: (show) => set((state) => { state.showModels = show; }),
    setShowMethods: (show) => set((state) => { state.showMethods = show; }),
    setShowHelp: (show) => set((state) => { state.showHelp = show; }),
    setShowSynthesizer: (show) => set((state) => { state.showSynthesizer = show; }),
    setShowStatus: (show) => set((state) => { state.showStatus = show; }),
    setShowTeamPreview: (show) => set((state) => { state.showTeamPreview = show; }),
    setShowExportSelector: (show) => set((state) => { state.showExportSelector = show; }),
    setShowAdvisor: (show) => set((state) => { state.showAdvisor = show; }),
    setShowLanguageSelector: (show) => set((state) => { state.showLanguageSelector = show; }),
    // Soft reload - clears screen and resets UI state
    softReload: () => {
        // Clear screen, scrollback buffer, and move cursor to home
        process.stdout.write(CLEAR_SCREEN);
        set((state) => {
            // Discussion state - clear ID first to invalidate any stale events
            state.currentDiscussionId = null;
            state.isDiscussionRunning = false;
            state.isDiscussionComplete = false;
            state.currentPhase = 0;
            state.previousPhase = 0;
            state.nextPhase = 0;
            state.currentMethod = "standard";
            state.totalPhases = 5;
            state.messages = [];
            state.isPaused = false;
            state.thinkingModel = null;
            state.currentQuestion = "";
            state.completedThinking = [];
            // Input state
            state.viewMode = "input";
            state.inputValue = "";
            state.historyIndex = -1;
            // Error state
            state.backendError = null;
            // Close all modals
            state.showModels = false;
            state.showMethods = false;
            state.showHelp = false;
            state.showSynthesizer = false;
            state.showStatus = false;
            state.showTeamPreview = false;
            state.showExportSelector = false;
            state.showAdvisor = false;
            state.showLanguageSelector = false;
        });
    },
})));
