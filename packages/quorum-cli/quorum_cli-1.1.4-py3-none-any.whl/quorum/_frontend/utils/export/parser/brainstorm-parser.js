/**
 * Brainstorm method parser.
 * 4 phases: Diverge (Wild Ideas) -> Build (Combine & Expand) -> Converge (Select & Refine) -> Synthesis
 */
import { BaseParser } from "./base-parser.js";
import { STRUCTURAL_PATTERNS } from "./types.js";
import { SCHEMA_VERSION, } from "../schemas/index.js";
export class BrainstormParser extends BaseParser {
    get methodName() {
        return "brainstorm";
    }
    get expectedPhaseCount() {
        return 4;
    }
    get validRoles() {
        return ["IDEATOR"];
    }
    parse() {
        const rawMetadata = this.parseRawMetadata();
        const question = this.parseQuestion();
        this.skipToDiscussion();
        const phases = this.parseAllPhases();
        // Parse synthesis and inject it into Phase 4
        this.skipToResult();
        const synthesisData = this.parseSynthesisData();
        // Find Phase 4 and populate it with synthesis
        const phase4 = phases.find(p => p.number === 4);
        if (phase4 && synthesisData) {
            phase4.messages = [{
                    source: synthesisData.synthesizer,
                    role: null,
                    content: synthesisData.content,
                    type: "synthesis",
                    ideasSelected: synthesisData.ideasSelected,
                    selectedIdeas: synthesisData.selectedIdeas,
                    alternativeDirections: synthesisData.alternativeDirections,
                }];
        }
        const metadata = {
            schemaVersion: SCHEMA_VERSION,
            exportedAt: new Date().toISOString(),
            method: "brainstorm",
            date: rawMetadata.date,
            models: rawMetadata.models,
            question,
        };
        const doc = {
            metadata,
            phases: phases,
            synthesis: synthesisData,
        };
        this.validate(doc);
        return { document: doc, warnings: this.warnings };
    }
    validate(doc) {
        if (doc.phases.length !== 4) {
            this.warn(`Expected 4 phases for Brainstorm method, found ${doc.phases.length}`);
        }
        if (doc.synthesis.ideasSelected === 0) {
            this.warn("No ideas selected in synthesis");
        }
    }
    parseAllPhases() {
        const phases = [];
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.RESULT.test(line))
                break;
            if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())
                break;
            const phaseHeader = this.parsePhaseHeader();
            if (phaseHeader) {
                const phase = this.parsePhase(phaseHeader.number, phaseHeader.title);
                phases.push(phase);
                continue;
            }
            this.consume();
        }
        return phases;
    }
    parsePhase(phaseNumber, phaseTitle) {
        switch (phaseNumber) {
            case 1: {
                const messages = this.parseIdeatorMessages(phaseNumber);
                return { number: 1, name: phaseTitle, messages };
            }
            case 2: {
                const messages = this.parseIdeatorMessages(phaseNumber);
                return { number: 2, name: phaseTitle, messages };
            }
            case 3: {
                const messages = this.parseIdeatorMessages(phaseNumber);
                return { number: 3, name: phaseTitle, messages };
            }
            case 4:
                // Phase 4 is synthesis - content is in Result section
                this.skipPhaseContent();
                return { number: 4, name: phaseTitle, messages: [] };
            default:
                this.warn(`Unexpected phase number ${phaseNumber} in Brainstorm method`);
                const messages = this.parseIdeatorMessages(phaseNumber);
                return { number: 1, name: phaseTitle, messages };
        }
    }
    skipPhaseContent() {
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.PHASE.test(line) ||
                STRUCTURAL_PATTERNS.RESULT.test(line) ||
                (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())) {
                break;
            }
            this.consume();
        }
    }
    parseIdeatorMessages(phaseNumber) {
        const messages = [];
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.PHASE.test(line) ||
                STRUCTURAL_PATTERNS.RESULT.test(line) ||
                (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())) {
                break;
            }
            const msgHeader = this.parseMessageHeader();
            if (msgHeader) {
                this.validateRole(msgHeader.role, phaseNumber);
                const content = this.collectMessageContent();
                messages.push({
                    source: msgHeader.source,
                    type: "ideation",
                    role: "IDEATOR",
                    content,
                });
                continue;
            }
            this.consume();
        }
        return messages;
    }
    parseSynthesisData() {
        const raw = this.parseRawSynthesis();
        const ideasSelected = this.parseIdeasCount(raw.consensus);
        const selectedIdeas = this.parseSelectedIdeas(raw.synthesis);
        return {
            synthesizer: raw.synthesizer,
            content: raw.synthesis,
            ideasSelected,
            selectedIdeas,
            alternativeDirections: raw.differences || null,
        };
    }
    parseIdeasCount(consensus) {
        // Match patterns like "3 SELECTED", "3 IDEAS SELECTED", "3 Idéer valda"
        const match = consensus.match(/(\d+)/);
        return match ? parseInt(match[1]) : 0;
    }
    parseSelectedIdeas(synthesis) {
        const ideas = [];
        // Try to extract structured ideas from synthesis
        // Look for numbered lists or "Idea X:" patterns
        const ideaPatterns = [
            /(?:^|\n)(?:##?\s*)?(?:Idea|Idé|Idee|Idée)\s*(\d+)[:\s]+([^\n]+)/gi,
            /(?:^|\n)(\d+)\.\s*\*\*([^*]+)\*\*/g,
            /(?:^|\n)(\d+)\.\s+([^\n]+)/g,
        ];
        for (const pattern of ideaPatterns) {
            let match;
            while ((match = pattern.exec(synthesis)) !== null) {
                const rank = parseInt(match[1]);
                const title = match[2].trim();
                // Avoid duplicates
                if (!ideas.find(i => i.rank === rank)) {
                    ideas.push({
                        rank,
                        title,
                        description: "", // Would need more context to extract
                        contributors: [], // Would need to track from messages
                    });
                }
            }
        }
        // Sort by rank
        ideas.sort((a, b) => a.rank - b.rank);
        return ideas;
    }
}
