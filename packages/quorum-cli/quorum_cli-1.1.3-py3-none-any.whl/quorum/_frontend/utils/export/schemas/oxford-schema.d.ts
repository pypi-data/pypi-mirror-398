/**
 * Oxford debate method JSON export schema
 * 4 phases: Opening Statements -> Rebuttals -> Closing Arguments -> Judgement
 */
import type { BaseMetadata, BasePhase, BaseMessage, BaseSynthesis, BaseExportDocument } from "./base-schema.js";
export type OxfordRole = "FOR" | "AGAINST";
export type OxfordRoundType = "opening" | "rebuttal" | "closing";
export type OxfordDecision = "FOR" | "AGAINST" | "PARTIAL";
export interface OxfordMetadata extends BaseMetadata {
    method: "oxford";
    teams: {
        for: string[];
        against: string[];
    };
}
/** Debate message with role and round type */
export interface OxfordDebateMessage extends BaseMessage {
    type: "debate";
    role: OxfordRole;
    roundType: OxfordRoundType;
}
export interface OxfordPhase1 extends BasePhase {
    number: 1;
    name: string;
    messages: OxfordDebateMessage[];
}
export interface OxfordPhase2 extends BasePhase {
    number: 2;
    name: string;
    messages: OxfordDebateMessage[];
}
export interface OxfordPhase3 extends BasePhase {
    number: 3;
    name: string;
    messages: OxfordDebateMessage[];
}
export interface OxfordJudgementMessage extends BaseMessage {
    type: "judgement";
    decision: OxfordDecision;
    keyContentions: string | null;
}
export interface OxfordPhase4 extends BasePhase {
    number: 4;
    name: string;
    messages: OxfordJudgementMessage[];
}
export interface OxfordJudgement extends BaseSynthesis {
    decision: OxfordDecision;
    keyContentions: string | null;
}
export interface OxfordExportDocument extends BaseExportDocument {
    metadata: OxfordMetadata;
    phases: [OxfordPhase1, OxfordPhase2, OxfordPhase3, OxfordPhase4];
    synthesis: OxfordJudgement;
}
