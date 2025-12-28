/**
 * Socratic method parser.
 * 3 phases: Initial Thesis -> Socratic Inquiry -> Aporia & Insights
 */
import { BaseParser } from "./base-parser.js";
import { STRUCTURAL_PATTERNS } from "./types.js";
import { SCHEMA_VERSION, } from "../schemas/index.js";
export class SocraticParser extends BaseParser {
    get methodName() {
        return "socratic";
    }
    get expectedPhaseCount() {
        return 3;
    }
    get validRoles() {
        return ["QUESTIONER", "RESPONDENT"];
    }
    parse() {
        const rawMetadata = this.parseRawMetadata();
        const question = this.parseQuestion();
        this.skipToDiscussion();
        const phases = this.parseAllPhases();
        // Extract respondent and questioners from messages
        const { respondent, questioners } = this.extractRoles(phases);
        // Parse synthesis and inject it into Phase 3
        this.skipToResult();
        const synthesisData = this.parseSynthesisData();
        // Find Phase 3 and add synthesis message
        const phase3 = phases.find(p => p.number === 3);
        if (phase3 && synthesisData) {
            // Add synthesis message to the end of Phase 3 (after dialogue messages)
            const synthesisMessage = {
                source: synthesisData.synthesizer,
                role: null,
                content: synthesisData.content,
                type: "synthesis",
                aporeaReached: synthesisData.aporeaReached,
                openQuestions: synthesisData.openQuestions,
            };
            phase3.messages.push(synthesisMessage);
        }
        const metadata = {
            schemaVersion: SCHEMA_VERSION,
            exportedAt: new Date().toISOString(),
            method: "socratic",
            date: rawMetadata.date,
            models: rawMetadata.models,
            question,
            respondent,
            questioners,
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
        if (doc.phases.length !== 3) {
            this.warn(`Expected 3 phases for Socratic method, found ${doc.phases.length}`);
        }
        if (!doc.metadata.respondent) {
            this.warn("No respondent identified");
        }
        if (doc.metadata.questioners.length === 0) {
            this.warn("No questioners identified");
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
        const messages = this.parseDialogueMessages(phaseNumber);
        switch (phaseNumber) {
            case 1:
                return { number: 1, name: phaseTitle, messages };
            case 2:
                return { number: 2, name: phaseTitle, messages };
            case 3:
                return { number: 3, name: phaseTitle, messages };
            default:
                this.warn(`Unexpected phase number ${phaseNumber} in Socratic method`);
                return { number: 1, name: phaseTitle, messages };
        }
    }
    parseDialogueMessages(phaseNumber) {
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
                    type: "dialogue",
                    role: msgHeader.role || "RESPONDENT",
                    content,
                });
                continue;
            }
            this.consume();
        }
        return messages;
    }
    extractRoles(phases) {
        const respondents = new Set();
        const questioners = new Set();
        for (const phase of phases) {
            for (const msg of phase.messages) {
                if (msg.role === "RESPONDENT") {
                    respondents.add(msg.source);
                }
                else if (msg.role === "QUESTIONER") {
                    questioners.add(msg.source);
                }
            }
        }
        return {
            respondent: Array.from(respondents)[0] || "",
            questioners: Array.from(questioners),
        };
    }
    parseSynthesisData() {
        const raw = this.parseRawSynthesis();
        return {
            synthesizer: raw.synthesizer,
            content: raw.synthesis,
            aporeaReached: this.normalizeAporea(raw.consensus),
            openQuestions: raw.differences || null,
        };
    }
    normalizeAporea(value) {
        const upper = value.toUpperCase();
        if (upper.includes("YES") || upper.includes("JA") || upper.includes("OUI") || upper.includes("SÍ") || upper.includes("SÌ")) {
            return "YES";
        }
        if (upper.includes("PARTIAL") || upper.includes("DELVIS") || upper.includes("TEILWEISE") || upper.includes("PARTIEL") || upper.includes("PARCIAL") || upper.includes("PARZIALE")) {
            return "PARTIAL";
        }
        return "NO";
    }
}
