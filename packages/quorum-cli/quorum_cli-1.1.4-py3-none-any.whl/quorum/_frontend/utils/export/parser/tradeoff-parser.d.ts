/**
 * Tradeoff analysis method parser.
 * 4 phases: Frame (Define Alternatives) -> Criteria -> Evaluate -> Decision
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type TradeoffExportDocument } from "../schemas/index.js";
export declare class TradeoffParser extends BaseParser<TradeoffExportDocument> {
    get methodName(): "tradeoff";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<TradeoffExportDocument>;
    validate(doc: TradeoffExportDocument): void;
    private parseAllPhases;
    private parsePhase;
    private parsePhase1;
    private parsePhase2;
    private parsePhase3;
    private parseEvaluatorMessages;
    private parseEvaluationMessages;
    private extractScores;
    private extractFramework;
    private parseDecisionData;
    private normalizeAgreement;
    private extractRecommendation;
}
