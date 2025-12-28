/**
 * Delphi method parser.
 * 3-4 phases: Round 1 -> Round 2 -> Round 3 (optional) -> Aggregation
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type DelphiExportDocument } from "../schemas/index.js";
export declare class DelphiParser extends BaseParser<DelphiExportDocument> {
    get methodName(): "delphi";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<DelphiExportDocument>;
    validate(doc: DelphiExportDocument): void;
    private parseAllPhases;
    private isAggregationPhase;
    private skipPhaseContent;
    private parseEstimates;
    private extractConfidenceFromContent;
    private countRounds;
    private parseAggregationData;
    private normalizeConvergence;
    private countConfidenceLevels;
}
