/**
 * Method-specific terminology registry for export formatting.
 * Single source of truth for all 7 discussion methods.
 * Uses i18n for translated labels.
 */
import { t } from "../../i18n/index.js";
/**
 * Static configuration for methods (non-translated properties).
 */
const METHOD_CONFIG = {
    standard: { showConsensus: true, bannerColor: "#065f46" },
    oxford: { showConsensus: true, bannerColor: "#7c3aed" },
    advocate: { showConsensus: false, bannerColor: "#991b1b" },
    socratic: { showConsensus: true, bannerColor: "#0e7490" },
    delphi: { showConsensus: true, bannerColor: "#7e22ce" },
    brainstorm: { showConsensus: true, bannerColor: "#0891b2" },
    tradeoff: { showConsensus: true, bannerColor: "#1d4ed8" },
};
/**
 * Get terminology for a discussion method.
 * Labels are dynamically translated using the current language.
 * @param method - The discussion method
 * @returns Method-specific terminology
 */
export function getMethodTerminology(method) {
    const config = METHOD_CONFIG[method];
    return {
        resultLabel: t(`terminology.result.${method}`),
        synthesisLabel: t(`terminology.synthesis.${method}`),
        differencesLabel: t(`terminology.differences.${method}`),
        byLabel: t(`terminology.by.${method}`),
        consensusLabel: config.showConsensus
            ? t(`terminology.consensus.${method}`)
            : "",
        showConsensus: config.showConsensus,
        bannerColor: config.bannerColor,
    };
}
/**
 * Get result label in uppercase (for plain text export).
 */
export function getResultLabelUppercase(method) {
    return t(`terminology.result.${method}`).toUpperCase();
}
