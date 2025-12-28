/**
 * Abstract base parser class with shared functionality for all method parsers.
 */
import type { BaseExportDocument, ParseResult, DiscussionMethod } from "../schemas/index.js";
import { type ParsedRole, type RawMetadata } from "./types.js";
/**
 * Abstract base parser that provides shared parsing functionality.
 * Each method-specific parser extends this class and implements its own validation.
 */
export declare abstract class BaseParser<T extends BaseExportDocument> {
    protected lines: string[];
    protected index: number;
    protected warnings: string[];
    constructor(markdown: string);
    /** Method name for validation messages */
    abstract get methodName(): DiscussionMethod;
    /** Expected phase count for this method */
    abstract get expectedPhaseCount(): number;
    /** Valid roles for this method */
    abstract get validRoles(): ParsedRole[];
    /** Parse the document with method-specific logic */
    abstract parse(): ParseResult<T>;
    /** Validate the parsed document against method constraints */
    abstract validate(doc: T): void;
    protected peek(): string;
    protected peekRaw(): string;
    protected consume(): string;
    protected consumeRaw(): string;
    protected skipEmpty(): void;
    protected hasMore(): boolean;
    protected savePosition(): number;
    protected restorePosition(pos: number): void;
    /** Add a validation warning without failing */
    protected warn(message: string): void;
    /** Throw validation error for fatal issues */
    protected error(message: string, phase?: number): never;
    /** Validate role is valid for this method */
    protected validateRole(role: ParsedRole, phase: number): void;
    /** Parse metadata section - shared across all methods */
    protected parseRawMetadata(): RawMetadata;
    /** Parse question section - shared across all methods */
    protected parseQuestion(): string;
    /** Skip to Discussion section */
    protected skipToDiscussion(): void;
    /** Skip to Result section */
    protected skipToResult(): boolean;
    /** Check if current line starts a new message or phase */
    protected isMessageOrPhaseEnd(): boolean;
    /** Look ahead to check if result section follows */
    protected looksLikeResultAhead(): boolean;
    /** Collect content until next section marker */
    protected collectUntilNextSection(): string;
    /** Collect message content until next message/phase/result */
    protected collectMessageContent(): string;
    /** Parse a phase header and return its components */
    protected parsePhaseHeader(): {
        number: number;
        title: string;
    } | null;
    /** Parse a message header and return its components */
    protected parseMessageHeader(): {
        source: string;
        role: ParsedRole;
        messageType: string | null;
    } | null;
    /** Check if a message type label indicates a critique */
    protected isCritiqueType(messageType: string | null): boolean;
    /** Check if a message type label indicates a final position */
    protected isPositionType(messageType: string | null): boolean;
    /** Parse critique fields (agreements/disagreements/missing) */
    protected parseCritiqueFields(): {
        agreements: string;
        disagreements: string;
        missing: string;
    };
    /** Parse position message with confidence */
    protected parsePositionContent(): {
        content: string;
        confidence: string;
    };
    /** Parse synthesis/result section - returns raw fields for method-specific processing */
    protected parseRawSynthesis(): {
        resultLabel: string;
        consensusLabel: string;
        consensus: string;
        byLabel: string;
        synthesizer: string;
        synthesisLabel: string;
        synthesis: string;
        differencesLabel: string;
        differences: string;
    };
}
