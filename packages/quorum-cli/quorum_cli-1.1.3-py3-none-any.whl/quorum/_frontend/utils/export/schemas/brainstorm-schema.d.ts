/**
 * Brainstorm method JSON export schema
 * 4 phases: Diverge (Wild Ideas) -> Build (Combine & Expand) -> Converge (Select & Refine) -> Synthesis
 */
import type { BaseMetadata, BasePhase, BaseMessage, BaseSynthesis, BaseExportDocument } from "./base-schema.js";
export interface BrainstormMetadata extends BaseMetadata {
    method: "brainstorm";
}
/** Ideator message for brainstorming */
export interface IdeatorMessage extends BaseMessage {
    type: "ideation";
    role: "IDEATOR";
}
export interface BrainstormPhase1 extends BasePhase {
    number: 1;
    name: string;
    messages: IdeatorMessage[];
}
export interface BrainstormPhase2 extends BasePhase {
    number: 2;
    name: string;
    messages: IdeatorMessage[];
}
export interface BrainstormPhase3 extends BasePhase {
    number: 3;
    name: string;
    messages: IdeatorMessage[];
}
export interface BrainstormSynthesisMessage extends BaseMessage {
    type: "synthesis";
    role: null;
    ideasSelected: number;
    selectedIdeas: SelectedIdea[];
    alternativeDirections: string | null;
}
export interface BrainstormPhase4 extends BasePhase {
    number: 4;
    name: string;
    messages: BrainstormSynthesisMessage[];
}
/** Selected idea from brainstorming */
export interface SelectedIdea {
    rank: number;
    title: string;
    description: string;
    contributors: string[];
}
export interface BrainstormSynthesis extends BaseSynthesis {
    ideasSelected: number;
    selectedIdeas: SelectedIdea[];
    alternativeDirections: string | null;
}
export interface BrainstormExportDocument extends BaseExportDocument {
    metadata: BrainstormMetadata;
    phases: [BrainstormPhase1, BrainstormPhase2, BrainstormPhase3, BrainstormPhase4];
    synthesis: BrainstormSynthesis;
}
