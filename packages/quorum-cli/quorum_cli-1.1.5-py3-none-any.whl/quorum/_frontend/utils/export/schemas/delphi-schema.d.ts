/**
 * Delphi method JSON export schema
 * 3-4 phases: Round 1 -> Round 2 -> Round 3 (optional) -> Aggregation
 */
import type { BaseMetadata, BasePhase, BaseMessage, BaseSynthesis, BaseExportDocument, ConfidenceLevel, ConfidenceBreakdown } from "./base-schema.js";
export type DelphiConvergence = "YES" | "PARTIAL" | "NO";
export interface DelphiMetadata extends BaseMetadata {
    method: "delphi";
    totalRounds: number;
}
/** Anonymous panelist estimate */
export interface DelphiEstimate extends BaseMessage {
    type: "estimate";
    role: "PANELIST";
    anonymous: true;
    panelistId: string;
    confidence?: ConfidenceLevel;
    revised?: boolean;
}
export interface DelphiRound extends BasePhase {
    name: string;
    messages: DelphiEstimate[];
}
export interface DelphiAggregationMessage extends BaseMessage {
    type: "aggregation";
    role: null;
    convergence: DelphiConvergence;
    confidenceDistribution: ConfidenceBreakdown;
    outlierPerspectives: string | null;
}
export interface DelphiAggregationPhase extends BasePhase {
    name: string;
    messages: DelphiAggregationMessage[];
}
export interface DelphiAggregation extends BaseSynthesis {
    convergence: DelphiConvergence;
    confidenceDistribution: ConfidenceBreakdown;
    outlierPerspectives: string | null;
}
export interface DelphiExportDocument extends BaseExportDocument {
    metadata: DelphiMetadata;
    phases: (DelphiRound | DelphiAggregationPhase)[];
    synthesis: DelphiAggregation;
}
