/**
 * Abstract base parser class with shared functionality for all method parsers.
 */
import { STRUCTURAL_PATTERNS, METADATA_PATTERNS, MESSAGE_TYPE_LABELS, ParserValidationError, } from "./types.js";
/**
 * Abstract base parser that provides shared parsing functionality.
 * Each method-specific parser extends this class and implements its own validation.
 */
export class BaseParser {
    lines;
    index;
    warnings;
    constructor(markdown) {
        this.lines = markdown.split("\n");
        this.index = 0;
        this.warnings = [];
    }
    // ============ State Helpers ============
    peek() {
        return this.lines[this.index]?.trim() ?? "";
    }
    peekRaw() {
        return this.lines[this.index] ?? "";
    }
    consume() {
        return this.lines[this.index++] ?? "";
    }
    consumeRaw() {
        return this.lines[this.index++] ?? "";
    }
    skipEmpty() {
        while (this.index < this.lines.length && !this.lines[this.index]?.trim()) {
            this.index++;
        }
    }
    hasMore() {
        return this.index < this.lines.length;
    }
    savePosition() {
        return this.index;
    }
    restorePosition(pos) {
        this.index = pos;
    }
    // ============ Validation Helpers ============
    /** Add a validation warning without failing */
    warn(message) {
        this.warnings.push(message);
    }
    /** Throw validation error for fatal issues */
    error(message, phase) {
        throw new ParserValidationError(this.methodName, message, phase);
    }
    /** Validate role is valid for this method */
    validateRole(role, phase) {
        if (role !== null && !this.validRoles.includes(role)) {
            this.warn(`Unexpected role "${role}" in phase ${phase} for ${this.methodName} method`);
        }
    }
    // ============ Shared Parsing Methods ============
    /** Parse metadata section - shared across all methods */
    parseRawMetadata() {
        const metadata = { date: "", method: "", models: [] };
        while (this.hasMore()) {
            const line = this.peek();
            const dateMatch = line.match(METADATA_PATTERNS.DATE);
            if (dateMatch) {
                metadata.date = dateMatch[2].trim();
                this.consume();
                continue;
            }
            const methodMatch = line.match(METADATA_PATTERNS.METHOD);
            if (methodMatch) {
                metadata.method = methodMatch[2].trim();
                this.consume();
                continue;
            }
            const modelsMatch = line.match(METADATA_PATTERNS.MODELS);
            if (modelsMatch) {
                metadata.models = modelsMatch[2].trim().split(",").map(m => m.trim());
                this.consume();
                continue;
            }
            if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) || STRUCTURAL_PATTERNS.QUESTION.test(line)) {
                break;
            }
            this.consume();
        }
        return metadata;
    }
    /** Parse question section - shared across all methods */
    parseQuestion() {
        // Skip to Question section
        while (this.hasMore() && !STRUCTURAL_PATTERNS.QUESTION.test(this.peek())) {
            this.consume();
        }
        this.consume(); // Skip "## Question"
        this.skipEmpty();
        // Parse question (blockquote)
        let question = "";
        if (this.peek().startsWith(">")) {
            question = this.consume().replace(/^>\s*/, "");
            while (this.hasMore() && this.peek().startsWith(">")) {
                question += " " + this.consume().replace(/^>\s*/, "");
            }
        }
        return question;
    }
    /** Skip to Discussion section */
    skipToDiscussion() {
        while (this.hasMore() && !STRUCTURAL_PATTERNS.DISCUSSION.test(this.peek())) {
            this.consume();
        }
        this.consume(); // Skip "## Discussion"
        this.skipEmpty();
    }
    /** Skip to Result section */
    skipToResult() {
        while (this.hasMore() && !STRUCTURAL_PATTERNS.RESULT.test(this.peek())) {
            this.consume();
        }
        return this.hasMore() && STRUCTURAL_PATTERNS.RESULT.test(this.peek());
    }
    /** Check if current line starts a new message or phase */
    isMessageOrPhaseEnd() {
        const line = this.peek();
        return (STRUCTURAL_PATTERNS.MESSAGE.test(line) ||
            STRUCTURAL_PATTERNS.PHASE.test(line) ||
            STRUCTURAL_PATTERNS.RESULT.test(line) ||
            (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead()));
    }
    /** Look ahead to check if result section follows */
    looksLikeResultAhead() {
        let lookAhead = this.index + 1;
        while (lookAhead < this.lines.length && !this.lines[lookAhead]?.trim()) {
            lookAhead++;
        }
        return lookAhead < this.lines.length && STRUCTURAL_PATTERNS.RESULT.test(this.lines[lookAhead].trim());
    }
    /** Collect content until next section marker */
    collectUntilNextSection() {
        const contentLines = [];
        while (this.hasMore() &&
            !STRUCTURAL_PATTERNS.AGREEMENTS.test(this.peek()) &&
            !STRUCTURAL_PATTERNS.DISAGREEMENTS.test(this.peek()) &&
            !STRUCTURAL_PATTERNS.MISSING.test(this.peek()) &&
            !this.isMessageOrPhaseEnd()) {
            contentLines.push(this.consume());
        }
        return contentLines.join("\n").trim();
    }
    /** Collect message content until next message/phase/result */
    collectMessageContent() {
        const contentLines = [];
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.MESSAGE.test(line) ||
                STRUCTURAL_PATTERNS.PHASE.test(line) ||
                STRUCTURAL_PATTERNS.RESULT.test(line) ||
                (STRUCTURAL_PATTERNS.SEPARATOR.test(line) && this.looksLikeResultAhead())) {
                break;
            }
            contentLines.push(this.consume());
        }
        return contentLines.join("\n").trim();
    }
    /** Parse a phase header and return its components */
    parsePhaseHeader() {
        const line = this.peek();
        const match = line.match(STRUCTURAL_PATTERNS.PHASE);
        if (!match)
            return null;
        this.consume();
        this.skipEmpty();
        return {
            number: parseInt(match[2]),
            title: line.replace(/^###\s*/, ""),
        };
    }
    /** Parse a message header and return its components */
    parseMessageHeader() {
        const line = this.peek();
        const match = line.match(STRUCTURAL_PATTERNS.MESSAGE);
        if (!match)
            return null;
        this.consume();
        this.skipEmpty();
        return {
            source: match[1].trim(),
            role: match[2] || null,
            messageType: match[3] || null,
        };
    }
    /** Check if a message type label indicates a critique */
    isCritiqueType(messageType) {
        return messageType !== null && MESSAGE_TYPE_LABELS.CRITIQUE.includes(messageType);
    }
    /** Check if a message type label indicates a final position */
    isPositionType(messageType) {
        return messageType !== null && MESSAGE_TYPE_LABELS.POSITION.includes(messageType);
    }
    /** Parse critique fields (agreements/disagreements/missing) */
    parseCritiqueFields() {
        const fields = { agreements: "", disagreements: "", missing: "" };
        while (this.hasMore() && !this.isMessageOrPhaseEnd()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.AGREEMENTS.test(line)) {
                this.consume();
                this.skipEmpty();
                fields.agreements = this.collectUntilNextSection();
            }
            else if (STRUCTURAL_PATTERNS.DISAGREEMENTS.test(line)) {
                this.consume();
                this.skipEmpty();
                fields.disagreements = this.collectUntilNextSection();
            }
            else if (STRUCTURAL_PATTERNS.MISSING.test(line)) {
                this.consume();
                this.skipEmpty();
                fields.missing = this.collectUntilNextSection();
            }
            else {
                this.consume();
            }
        }
        return fields;
    }
    /** Parse position message with confidence */
    parsePositionContent() {
        const contentLines = [];
        let confidence = "";
        while (this.hasMore() && !this.isMessageOrPhaseEnd()) {
            const line = this.peek();
            const confMatch = line.match(STRUCTURAL_PATTERNS.CONFIDENCE);
            if (confMatch) {
                confidence = confMatch[2].trim();
                this.consume();
            }
            else {
                contentLines.push(this.consume());
            }
        }
        return {
            content: contentLines.join("\n").trim(),
            confidence,
        };
    }
    /** Parse synthesis/result section - returns raw fields for method-specific processing */
    parseRawSynthesis() {
        const result = {
            resultLabel: "",
            consensusLabel: "",
            consensus: "",
            byLabel: "",
            synthesizer: "",
            synthesisLabel: "",
            synthesis: "",
            differencesLabel: "",
            differences: "",
        };
        // Get result header
        const resultMatch = this.peek().match(STRUCTURAL_PATTERNS.RESULT);
        result.resultLabel = resultMatch ? resultMatch[1] : "Result";
        this.consume();
        this.skipEmpty();
        while (this.hasMore()) {
            const line = this.peek();
            if (STRUCTURAL_PATTERNS.SEPARATOR.test(line) || STRUCTURAL_PATTERNS.FOOTER.test(line)) {
                break;
            }
            const consMatch = line.match(STRUCTURAL_PATTERNS.CONSENSUS_LINE);
            if (consMatch) {
                result.consensusLabel = consMatch[1];
                result.consensus = consMatch[2].trim();
                this.consume();
                continue;
            }
            const synthMatch = line.match(STRUCTURAL_PATTERNS.SYNTHESIZER_LINE);
            if (synthMatch) {
                result.byLabel = synthMatch[1];
                result.synthesizer = synthMatch[2].trim();
                this.consume();
                continue;
            }
            const synthHeaderMatch = line.match(STRUCTURAL_PATTERNS.SYNTHESIS_HEADER);
            if (synthHeaderMatch) {
                result.synthesisLabel = synthHeaderMatch[1];
                this.consume();
                this.skipEmpty();
                const synthLines = [];
                while (this.hasMore() &&
                    !STRUCTURAL_PATTERNS.DIFFERENCES_HEADER.test(this.peek()) &&
                    !STRUCTURAL_PATTERNS.FOOTER.test(this.peek())) {
                    synthLines.push(this.consume());
                }
                result.synthesis = synthLines.join("\n").trim();
                continue;
            }
            const diffHeaderMatch = line.match(STRUCTURAL_PATTERNS.DIFFERENCES_HEADER);
            if (diffHeaderMatch) {
                result.differencesLabel = diffHeaderMatch[1];
                this.consume();
                this.skipEmpty();
                const diffLines = [];
                while (this.hasMore() &&
                    !STRUCTURAL_PATTERNS.SEPARATOR.test(this.peek()) &&
                    !STRUCTURAL_PATTERNS.FOOTER.test(this.peek())) {
                    diffLines.push(this.consume());
                }
                result.differences = diffLines.join("\n").trim();
                continue;
            }
            this.consume();
        }
        return result;
    }
}
