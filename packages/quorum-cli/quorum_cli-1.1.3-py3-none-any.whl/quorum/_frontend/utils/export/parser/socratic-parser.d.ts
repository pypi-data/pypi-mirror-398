/**
 * Socratic method parser.
 * 3 phases: Initial Thesis -> Socratic Inquiry -> Aporia & Insights
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type SocraticExportDocument } from "../schemas/index.js";
export declare class SocraticParser extends BaseParser<SocraticExportDocument> {
    get methodName(): "socratic";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<SocraticExportDocument>;
    validate(doc: SocraticExportDocument): void;
    private parseAllPhases;
    private parsePhase;
    private parseDialogueMessages;
    private extractRoles;
    private parseSynthesisData;
    private normalizeAporea;
}
