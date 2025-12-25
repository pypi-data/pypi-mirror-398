/**
 * Standard method JSON export schema
 * 5 phases: Independent Answers -> Critique -> Discussion -> Final Positions -> Synthesis
 */
import type { BaseMetadata, BasePhase, BaseMessage, BaseSynthesis, BaseExportDocument, ConfidenceLevel, ConfidenceBreakdown } from "./base-schema.js";
export interface StandardMetadata extends BaseMetadata {
    method: "standard";
}
/** Phase 1: Independent answer from a model */
export interface StandardIndependentAnswer extends BaseMessage {
    type: "answer";
    role: null;
}
/** Phase 2: Structured critique with agreements/disagreements/missing */
export interface StandardCritique extends BaseMessage {
    type: "critique";
    role: null;
    agreements: string;
    disagreements: string;
    missing: string;
}
/** Phase 3: Discussion message */
export interface StandardDiscussionMessage extends BaseMessage {
    type: "discussion";
    role: null;
}
/** Phase 4: Final position with confidence level */
export interface StandardFinalPosition extends BaseMessage {
    type: "position";
    role: null;
    confidence: ConfidenceLevel;
}
export interface StandardPhase1 extends BasePhase {
    number: 1;
    name: string;
    messages: StandardIndependentAnswer[];
}
export interface StandardPhase2 extends BasePhase {
    number: 2;
    name: string;
    messages: StandardCritique[];
}
export interface StandardPhase3 extends BasePhase {
    number: 3;
    name: string;
    messages: StandardDiscussionMessage[];
}
export interface StandardPhase4 extends BasePhase {
    number: 4;
    name: string;
    messages: StandardFinalPosition[];
}
export interface StandardSynthesisMessage extends BaseMessage {
    type: "synthesis";
    consensus: StandardConsensus;
    differences: string | null;
    confidenceBreakdown: ConfidenceBreakdown;
}
export interface StandardPhase5 extends BasePhase {
    number: 5;
    name: string;
    messages: StandardSynthesisMessage[];
}
export type StandardConsensus = "YES" | "PARTIAL" | "NO";
export interface StandardSynthesis extends BaseSynthesis {
    consensus: StandardConsensus;
    differences: string | null;
    confidenceBreakdown: ConfidenceBreakdown;
}
export interface StandardExportDocument extends BaseExportDocument {
    metadata: StandardMetadata;
    phases: [StandardPhase1, StandardPhase2, StandardPhase3, StandardPhase4, StandardPhase5];
    synthesis: StandardSynthesis;
}
