/**
 * Devil's Advocate method parser.
 * 3 phases: Initial Positions -> Cross-Examination -> Verdict
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type AdvocateExportDocument } from "../schemas/index.js";
export declare class AdvocateParser extends BaseParser<AdvocateExportDocument> {
    get methodName(): "advocate";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<AdvocateExportDocument>;
    validate(doc: AdvocateExportDocument): void;
    private parseAllPhases;
    private parsePhase;
    private parsePhase1;
    private parsePhase2;
    private extractRoles;
    private parseVerdictData;
}
