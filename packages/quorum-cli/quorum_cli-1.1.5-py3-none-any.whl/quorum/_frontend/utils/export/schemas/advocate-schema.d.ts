/**
 * Devil's Advocate method JSON export schema
 * 3 phases: Initial Positions -> Cross-Examination -> Verdict
 */
import type { BaseMetadata, BasePhase, BaseMessage, BaseSynthesis, BaseExportDocument } from "./base-schema.js";
export type AdvocateRole = "ADVOCATE" | "DEFENDER";
export interface AdvocateMetadata extends BaseMetadata {
    method: "advocate";
    advocate: string;
    defenders: string[];
}
/** Defender's initial position */
export interface DefenderPosition extends BaseMessage {
    type: "position";
    role: "DEFENDER";
}
/** Cross-examination message (question from advocate or response from defender) */
export interface CrossExaminationMessage extends BaseMessage {
    type: "examination";
    role: AdvocateRole;
    targetDefender?: string;
}
export interface AdvocatePhase1 extends BasePhase {
    number: 1;
    name: string;
    messages: DefenderPosition[];
}
export interface AdvocatePhase2 extends BasePhase {
    number: 2;
    name: string;
    messages: CrossExaminationMessage[];
}
export interface AdvocateVerdictMessage extends BaseMessage {
    type: "verdict";
    role: "ADVOCATE";
    unresolvedQuestions: string | null;
}
export interface AdvocatePhase3 extends BasePhase {
    number: 3;
    name: string;
    messages: AdvocateVerdictMessage[];
}
export interface AdvocateVerdict extends BaseSynthesis {
    unresolvedQuestions: string | null;
}
export interface AdvocateExportDocument extends BaseExportDocument {
    metadata: AdvocateMetadata;
    phases: [AdvocatePhase1, AdvocatePhase2, AdvocatePhase3];
    synthesis: AdvocateVerdict;
}
