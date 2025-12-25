/**
 * PDF rendering for Quorum discussion exports.
 * Uses method-aware parser structure for consistent rendering.
 */
import type { BaseExportDocument } from "./schemas/base-schema.js";
declare const PDF_CONFIG: {
    pageWidth: number;
    contentWidth: number;
    leftMargin: number;
    pageBreakThreshold: number;
    messagePageBreak: number;
    colors: {
        title: string;
        header: string;
        metaBox: string;
        metaText: string;
        questionBg: string;
        questionAccent: string;
        questionText: string;
        bodyText: string;
        muted: string;
        footer: string;
        footerLine: string;
        critique: string;
        position: string;
        agreements: string;
        disagreements: string;
        missing: string;
        differences: string;
        for: string;
        against: string;
        questioner: string;
        respondent: string;
        panelist: string;
        ideator: string;
        evaluator: string;
        neutral: string;
    };
};
/**
 * PDF Renderer for Quorum discussion documents.
 * Works with method-aware parser structure.
 */
export declare class PDFRenderer {
    private doc;
    private formatModelName;
    private renderMarkdown;
    private method;
    constructor(doc: PDFKit.PDFDocument, formatModelName: (id: string) => string, renderMarkdown: (doc: PDFKit.PDFDocument, text: string, width?: number) => void);
    /**
     * Render a complete discussion document to PDF.
     */
    render(document: BaseExportDocument): void;
    /**
     * Render document header with title and metadata box.
     */
    private renderHeader;
    /**
     * Render the question section with styled blockquote.
     */
    private renderQuestion;
    /**
     * Render the "Discussion" section header.
     */
    private renderDiscussionHeader;
    /**
     * Render all phases with their messages.
     * The last phase contains synthesis which is rendered specially.
     */
    private renderPhases;
    /**
     * Render a single phase with its messages.
     */
    private renderPhase;
    /**
     * Render a single message based on its type.
     */
    private renderMessage;
    /**
     * Render a critique message with agreements/disagreements/missing sections.
     */
    private renderCritiqueMessage;
    /**
     * Render a final position message with confidence indicator.
     */
    private renderPositionMessage;
    /**
     * Render a regular answer/chat message.
     */
    private renderAnswerMessage;
    /**
     * Render the synthesis phase (last phase) with special result styling.
     */
    private renderSynthesisPhase;
    /**
     * Extract consensus/decision value from method-specific synthesis.
     */
    private getConsensusValue;
    /**
     * Extract differences value from method-specific synthesis.
     */
    private getDifferencesValue;
    /**
     * Get consensus color based on method and value.
     */
    private getConsensusColor;
    /**
     * Render the document footer.
     */
    private renderFooter;
}
/** PDF configuration export for external use */
export { PDF_CONFIG };
