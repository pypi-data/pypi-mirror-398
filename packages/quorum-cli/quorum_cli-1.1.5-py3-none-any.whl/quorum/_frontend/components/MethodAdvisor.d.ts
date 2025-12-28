/**
 * Method Advisor - AI-powered method recommendation panel.
 * Triggered by Tab key, analyzes a question and recommends the best discussion method.
 */
import type { DiscussionMethod } from "../store/index.js";
import type { AnalyzeQuestionResult } from "../ipc/protocol.js";
interface MethodAdvisorProps {
    onSelect: (method: DiscussionMethod, question: string) => void;
    onCancel: () => void;
    analyzeQuestion: (question: string) => Promise<AnalyzeQuestionResult>;
}
export declare function MethodAdvisor({ onSelect, onCancel, analyzeQuestion }: MethodAdvisorProps): import("react/jsx-runtime").JSX.Element;
export {};
