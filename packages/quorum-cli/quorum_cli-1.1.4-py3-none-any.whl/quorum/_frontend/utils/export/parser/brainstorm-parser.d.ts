/**
 * Brainstorm method parser.
 * 4 phases: Diverge (Wild Ideas) -> Build (Combine & Expand) -> Converge (Select & Refine) -> Synthesis
 */
import { BaseParser } from "./base-parser.js";
import type { ParsedRole } from "./types.js";
import { type ParseResult, type BrainstormExportDocument } from "../schemas/index.js";
export declare class BrainstormParser extends BaseParser<BrainstormExportDocument> {
    get methodName(): "brainstorm";
    get expectedPhaseCount(): number;
    get validRoles(): ParsedRole[];
    parse(): ParseResult<BrainstormExportDocument>;
    validate(doc: BrainstormExportDocument): void;
    private parseAllPhases;
    private parsePhase;
    private skipPhaseContent;
    private parseIdeatorMessages;
    private parseSynthesisData;
    private parseIdeasCount;
    private parseSelectedIdeas;
}
