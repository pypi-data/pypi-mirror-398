/**
 * Delphi method parser.
 * 3-4 phases: Round 1 -> Round 2 -> Round 3 (optional) -> Aggregation
 */
import { BaseParser } from "./base-parser.js";
import { STRUCTURAL_PATTERNS } from "./types.js";
import { SCHEMA_VERSION, } from "../schemas/index.js";
export class DelphiParser extends BaseParser {
    get methodName() {
        return "delphi";
    }
    get expectedPhaseCount() {
        return 4; // Can be 3-4 depending on convergence
    }
    get validRoles() {
        return ["PANELIST"];
    }
    parse() {
        const rawMetadata = this.parseRawMetadata();
        const question = this.parseQuestion();
        this.skipToDiscussion();
        const phases = this.parseAllPhases();
        // Parse aggregation and inject it into the last phase
        this.skipToResult();
        const aggregationData = this.parseAggregationData(phases);
        // Find aggregation phase (last phase) and populate it
        const aggregationPhase = phases.find(p => this.isAggregationPhase(p.name));
        if (aggregationPhase && aggregationData) {
            aggregationPhase.messages = [{
                    source: aggregationData.synthesizer,
                    role: null,
                    content: aggregationData.content,
                    type: "aggregation",
                    convergence: aggregationData.convergence,
                    confidenceDistribution: aggregationData.confidenceDistribution,
                    outlierPerspectives: aggregationData.outlierPerspectives,
                }];
        }
        const metadata = {
            schemaVersion: SCHEMA_VERSION,
            exportedAt: new Date().toISOString(),
            method: "delphi",
            date: rawMetadata.date,
            models: rawMetadata.models,
            question,
            totalRounds: this.countRounds(phases),
        };
        const doc = {
            metadata,
            phases,
            synthesis: aggregationData,
        };
        this.validate(doc);
        return { document: doc, warnings: this.warnings };
    }
    validate(doc) {
        if (doc.phases.length < 3 || doc.phases.length > 4) {
            this.warn(`Expected 3-4 phases for Delphi method, found ${doc.phases.length}`);
        }
        // Validate estimates are anonymous
        for (const phase of doc.phases) {
            if ("messages" in phase && phase.messages) {
                for (const msg of phase.messages) {
                    if (!msg.panelistId) {
                        this.warn(`Estimate missing anonymous panelist ID`);
                    }
                }
            }
        }
    }
    parseAllPhases() {
        const phases = [];
        let panelistCounter = 0;
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.RESULT.test(line))
                break;
            if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())
                break;
            const phaseHeader = this.parsePhaseHeader();
            if (phaseHeader) {
                // Check if this is the aggregation phase (usually last)
                const isAggregation = this.isAggregationPhase(phaseHeader.title);
                if (isAggregation) {
                    // Skip content - aggregation is in synthesis
                    this.skipPhaseContent();
                    phases.push({
                        number: phaseHeader.number,
                        name: phaseHeader.title,
                        messages: [],
                    });
                }
                else {
                    const messages = this.parseEstimates(phaseHeader.number, panelistCounter);
                    phases.push({
                        number: phaseHeader.number,
                        name: phaseHeader.title,
                        messages,
                    });
                }
                continue;
            }
            this.consume();
        }
        return phases;
    }
    isAggregationPhase(title) {
        const lower = title.toLowerCase();
        return (lower.includes("aggregat") ||
            lower.includes("synthesis") ||
            lower.includes("final") ||
            lower.includes("slut") ||
            lower.includes("schluss"));
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
    parseEstimates(phaseNumber, startCounter) {
        const messages = [];
        let panelistIndex = startCounter;
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
                const confidence = this.extractConfidenceFromContent(content);
                // Assign anonymous panelist ID
                const panelistId = String.fromCharCode(65 + panelistIndex); // A, B, C, ...
                panelistIndex++;
                messages.push({
                    source: msgHeader.source,
                    type: "estimate",
                    role: "PANELIST",
                    content,
                    anonymous: true,
                    panelistId,
                    confidence: confidence || undefined,
                    revised: phaseNumber > 1,
                });
                continue;
            }
            this.consume();
        }
        return messages;
    }
    extractConfidenceFromContent(content) {
        const upper = content.toUpperCase();
        if (upper.includes("HIGH") || upper.includes("HÖG") || upper.includes("HOCH")) {
            return "HIGH";
        }
        if (upper.includes("MEDIUM") || upper.includes("MEDEL") || upper.includes("MITTEL")) {
            return "MEDIUM";
        }
        if (upper.includes("LOW") || upper.includes("LÅG") || upper.includes("NIEDRIG")) {
            return "LOW";
        }
        return null;
    }
    countRounds(phases) {
        return phases.filter(p => p.messages?.length > 0).length;
    }
    parseAggregationData(phases) {
        const raw = this.parseRawSynthesis();
        const confidenceDistribution = this.countConfidenceLevels(phases);
        return {
            synthesizer: raw.synthesizer,
            content: raw.synthesis,
            convergence: this.normalizeConvergence(raw.consensus),
            confidenceDistribution,
            outlierPerspectives: raw.differences || null,
        };
    }
    normalizeConvergence(value) {
        const upper = value.toUpperCase();
        if (upper.includes("YES") || upper.includes("JA") || upper.includes("OUI")) {
            return "YES";
        }
        if (upper.includes("PARTIAL") || upper.includes("DELVIS") || upper.includes("TEILWEISE")) {
            return "PARTIAL";
        }
        return "NO";
    }
    countConfidenceLevels(phases) {
        const breakdown = { HIGH: 0, MEDIUM: 0, LOW: 0 };
        for (const phase of phases) {
            if ("messages" in phase && phase.messages) {
                for (const msg of phase.messages) {
                    if (msg.confidence === "HIGH")
                        breakdown.HIGH++;
                    else if (msg.confidence === "MEDIUM")
                        breakdown.MEDIUM++;
                    else if (msg.confidence === "LOW")
                        breakdown.LOW++;
                }
            }
        }
        return breakdown;
    }
}
