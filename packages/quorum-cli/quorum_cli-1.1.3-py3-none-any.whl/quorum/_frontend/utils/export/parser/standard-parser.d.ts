/**
 * Standard method parser.
 * 5 phases: Independent Answers -> Critique -> Discussion -> Final Positions -> Synthesis
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type StandardExportDocument } from "../schemas/index.js";
export declare class StandardParser extends BaseParser<StandardExportDocument> {
    get methodName(): "standard";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<StandardExportDocument>;
    validate(doc: StandardExportDocument): void;
    private parseAllPhases;
    private parsePhase;
    private parsePhase1;
    private parsePhase2;
    private parsePhase3;
    private parsePhase4;
    private parsePhase5;
    private parseSynthesisData;
    private normalizeConsensus;
    private normalizeConfidence;
    private countConfidenceLevels;
}
