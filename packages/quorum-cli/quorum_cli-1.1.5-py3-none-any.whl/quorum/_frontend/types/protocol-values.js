/**
 * Centralized type definitions for protocol values exchanged between backend and frontend.
 * These types ensure type safety and provide translation key mappings for i18n.
 */
/** Translation key mapping for confidence levels */
export const CONFIDENCE_KEYS = {
    HIGH: "msg.confidence.high",
    MEDIUM: "msg.confidence.medium",
    LOW: "msg.confidence.low",
};
/** Translation key mapping for standard consensus values */
export const CONSENSUS_KEYS = {
    YES: "consensus.yes",
    NO: "consensus.no",
    PARTIAL: "consensus.partial",
};
/** Translation key mapping for role values */
export const ROLE_KEYS = {
    FOR: "role.for",
    AGAINST: "role.against",
    ADVOCATE: "role.advocate",
    DEFENDER: "role.defender",
    QUESTIONER: "role.questioner",
    RESPONDENT: "role.respondent",
    PANELIST: "role.panelist",
    IDEATOR: "role.ideator",
    EVALUATOR: "role.evaluator",
};
// =============================================================================
// Type Guards
// =============================================================================
/** Check if a string is a valid ConfidenceLevel */
export function isConfidenceLevel(value) {
    return value === "HIGH" || value === "MEDIUM" || value === "LOW";
}
/** Check if a string is a valid StandardConsensus */
export function isStandardConsensus(value) {
    return value === "YES" || value === "NO" || value === "PARTIAL";
}
/** Check if a string is a valid RoleValue */
export function isRoleValue(value) {
    return value !== null && value !== undefined && value in ROLE_KEYS;
}
