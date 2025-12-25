/**
 * Devil's Advocate method parser.
 * 3 phases: Initial Positions -> Cross-Examination -> Verdict
 */
import { BaseParser } from "./base-parser.js";
import { STRUCTURAL_PATTERNS } from "./types.js";
import { SCHEMA_VERSION, } from "../schemas/index.js";
export class AdvocateParser extends BaseParser {
    get methodName() {
        return "advocate";
    }
    get expectedPhaseCount() {
        return 3;
    }
    get validRoles() {
        return ["ADVOCATE", "DEFENDER"];
    }
    parse() {
        const rawMetadata = this.parseRawMetadata();
        const question = this.parseQuestion();
        this.skipToDiscussion();
        const phases = this.parseAllPhases();
        // Extract advocate and defenders from messages
        const { advocate, defenders } = this.extractRoles(phases);
        // Parse verdict and inject it into Phase 3
        this.skipToResult();
        const verdictData = this.parseVerdictData();
        // Find Phase 3 and populate it with verdict
        const phase3 = phases.find(p => p.number === 3);
        if (phase3 && verdictData) {
            phase3.messages = [{
                    source: verdictData.synthesizer,
                    role: "ADVOCATE",
                    content: verdictData.content,
                    type: "verdict",
                    unresolvedQuestions: verdictData.unresolvedQuestions,
                }];
        }
        const metadata = {
            schemaVersion: SCHEMA_VERSION,
            exportedAt: new Date().toISOString(),
            method: "advocate",
            date: rawMetadata.date,
            models: rawMetadata.models,
            question,
            advocate: advocate || verdictData.synthesizer,
            defenders,
        };
        const doc = {
            metadata,
            phases: phases,
            synthesis: verdictData,
        };
        this.validate(doc);
        return { document: doc, warnings: this.warnings };
    }
    validate(doc) {
        if (doc.phases.length !== 3) {
            this.warn(`Expected 3 phases for Advocate method, found ${doc.phases.length}`);
        }
        if (!doc.metadata.advocate) {
            this.warn("No advocate identified");
        }
        if (doc.metadata.defenders.length === 0) {
            this.warn("No defenders identified");
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
            case 1:
                return this.parsePhase1(phaseTitle);
            case 2:
                return this.parsePhase2(phaseTitle);
            case 3:
                return { number: 3, name: phaseTitle, messages: [] };
            default:
                this.warn(`Unexpected phase number ${phaseNumber} in Advocate method`);
                return this.parsePhase1(phaseTitle);
        }
    }
    parsePhase1(title) {
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
                this.validateRole(msgHeader.role, 1);
                const content = this.collectMessageContent();
                messages.push({
                    source: msgHeader.source,
                    type: "position",
                    role: "DEFENDER",
                    content,
                });
                continue;
            }
            this.consume();
        }
        return { number: 1, name: title, messages };
    }
    parsePhase2(title) {
        const messages = [];
        let currentDefender;
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.PHASE.test(line) ||
                STRUCTURAL_PATTERNS.RESULT.test(line) ||
                (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())) {
                break;
            }
            const msgHeader = this.parseMessageHeader();
            if (msgHeader) {
                this.validateRole(msgHeader.role, 2);
                const content = this.collectMessageContent();
                const role = msgHeader.role || "DEFENDER";
                // Track which defender is being examined
                if (role === "DEFENDER") {
                    currentDefender = msgHeader.source;
                }
                messages.push({
                    source: msgHeader.source,
                    type: "examination",
                    role,
                    content,
                    ...(role === "ADVOCATE" && currentDefender ? { targetDefender: currentDefender } : {}),
                });
                continue;
            }
            this.consume();
        }
        return { number: 2, name: title, messages };
    }
    extractRoles(phases) {
        const advocates = new Set();
        const defenders = new Set();
        for (const phase of phases) {
            for (const msg of phase.messages) {
                if (msg.role === "ADVOCATE") {
                    advocates.add(msg.source);
                }
                else if (msg.role === "DEFENDER") {
                    defenders.add(msg.source);
                }
            }
        }
        return {
            advocate: Array.from(advocates)[0] || "",
            defenders: Array.from(defenders),
        };
    }
    parseVerdictData() {
        const raw = this.parseRawSynthesis();
        return {
            synthesizer: raw.synthesizer,
            content: raw.synthesis,
            unresolvedQuestions: raw.differences || null,
        };
    }
}
