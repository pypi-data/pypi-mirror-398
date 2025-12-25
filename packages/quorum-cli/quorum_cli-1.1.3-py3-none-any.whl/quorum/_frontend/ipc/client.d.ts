/**
 * IPC Client for communicating with Quorum Python backend.
 */
import { EventEmitter } from "node:events";
import type { InitializeResult, ListModelsResult, ValidateModelResult, UserSettings, RunDiscussionParams, RunDiscussionResult, RoleAssignments, AnalyzeQuestionResult, GetConfigResult, EventMap, EventType } from "./protocol.js";
type EventListener<T extends EventType> = (params: EventMap[T]) => void;
export declare class BackendClient extends EventEmitter {
    private process;
    private readline;
    private pendingRequests;
    private isReady;
    private readyPromise;
    private readyResolve;
    private pythonCommand;
    private pythonArgs;
    constructor();
    /**
     * Start the backend process.
     */
    start(): Promise<void>;
    /**
     * Stop the backend process.
     */
    stop(): void;
    /**
     * Handle a line of output from the backend.
     */
    private handleLine;
    /**
     * Send a request and wait for response.
     */
    private request;
    initialize(): Promise<InitializeResult>;
    listModels(): Promise<ListModelsResult>;
    validateModel(modelId: string): Promise<ValidateModelResult>;
    getConfig(): Promise<GetConfigResult>;
    getUserSettings(): Promise<UserSettings>;
    saveUserSettings(settings: Partial<UserSettings>): Promise<void>;
    getInputHistory(): Promise<string[]>;
    addToInputHistory(input: string): Promise<void>;
    runDiscussion(params: RunDiscussionParams): Promise<RunDiscussionResult>;
    cancelDiscussion(): Promise<void>;
    resumeDiscussion(): Promise<void>;
    getRoleAssignments(method: string, modelIds: string[]): Promise<RoleAssignments | null>;
    swapRoleAssignments(assignments: RoleAssignments): Promise<RoleAssignments>;
    analyzeQuestion(question: string): Promise<AnalyzeQuestionResult>;
    onEvent<T extends EventType>(event: T, listener: EventListener<T>): this;
    offEvent<T extends EventType>(event: T, listener: EventListener<T>): this;
}
export {};
