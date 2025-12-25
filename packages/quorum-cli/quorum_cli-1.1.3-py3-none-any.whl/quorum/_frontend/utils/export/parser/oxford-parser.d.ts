/**
 * Oxford debate method parser.
 * 4 phases: Opening Statements -> Rebuttals -> Closing Arguments -> Judgement
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type OxfordExportDocument } from "../schemas/index.js";
export declare class OxfordParser extends BaseParser<OxfordExportDocument> {
    get methodName(): "oxford";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<OxfordExportDocument>;
    validate(doc: OxfordExportDocument): void;
    private parseAllPhases;
    private parsePhase;
    private getRoundType;
    private parseDebateMessages;
    private extractTeams;
    private parseJudgementData;
    private normalizeDecision;
}
