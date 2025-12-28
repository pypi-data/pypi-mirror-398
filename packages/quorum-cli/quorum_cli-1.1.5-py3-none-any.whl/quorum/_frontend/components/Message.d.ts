/**
 * Message display components for different message types.
 */
import React from "react";
import { type DiscussionMessage, type DiscussionMethod } from "../store/index.js";
export { getModelDisplayName } from "../utils/modelName.js";
interface PhaseMarkerProps {
    phase: number;
    messageKey: string;
    params?: Record<string, string>;
}
export declare function PhaseMarker({ phase, messageKey, params }: PhaseMarkerProps): import("react/jsx-runtime").JSX.Element;
interface IndependentAnswerProps {
    source: string;
    content: string;
}
export declare function IndependentAnswer({ source, content }: IndependentAnswerProps): import("react/jsx-runtime").JSX.Element;
interface CritiqueProps {
    source: string;
    agreements: string;
    disagreements: string;
    missing: string;
}
export declare function Critique({ source, agreements, disagreements, missing }: CritiqueProps): import("react/jsx-runtime").JSX.Element;
interface ChatMessageProps {
    source: string;
    content: string;
    role?: string | null;
    roundType?: string | null;
}
export declare function ChatMessage({ source, content, role, roundType }: ChatMessageProps): import("react/jsx-runtime").JSX.Element;
interface FinalPositionProps {
    source: string;
    position: string;
    confidence: string;
}
export declare function FinalPosition({ source, position, confidence }: FinalPositionProps): import("react/jsx-runtime").JSX.Element;
interface SynthesisProps {
    consensus: string;
    synthesis: string;
    differences: string;
    synthesizerModel: string;
    confidenceBreakdown?: Record<string, number>;
    method?: string;
}
export declare function Synthesis({ consensus, synthesis, differences, synthesizerModel, confidenceBreakdown, method, }: SynthesisProps): import("react/jsx-runtime").JSX.Element;
interface DiscussionHeaderProps {
    method: DiscussionMethod;
    models: string[];
    roleAssignments?: Record<string, string[]>;
}
export declare function DiscussionHeader({ method, models, roleAssignments }: DiscussionHeaderProps): import("react/jsx-runtime").JSX.Element;
interface MessageProps {
    message: DiscussionMessage;
}
/**
 * Memoized Message component to prevent unnecessary re-renders.
 * Only re-renders when the message prop actually changes.
 */
export declare const Message: React.NamedExoticComponent<MessageProps>;
