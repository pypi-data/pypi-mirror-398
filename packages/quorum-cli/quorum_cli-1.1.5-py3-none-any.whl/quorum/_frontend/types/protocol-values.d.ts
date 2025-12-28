/**
 * Centralized type definitions for protocol values exchanged between backend and frontend.
 * These types ensure type safety and provide translation key mappings for i18n.
 */
import type { TranslationKey } from "../i18n/index.js";
/** Confidence levels from backend FinalPositionEvent */
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";
/** Translation key mapping for confidence levels */
export declare const CONFIDENCE_KEYS: Record<ConfidenceLevel, TranslationKey>;
/** Standard consensus values (Standard, Socratic, Delphi, Advocate, Tradeoff) */
export type StandardConsensus = "YES" | "NO" | "PARTIAL";
/** Oxford method consensus values */
export type OxfordConsensus = "FOR" | "AGAINST";
/** All possible consensus values */
export type ConsensusValue = StandardConsensus | OxfordConsensus;
/** Translation key mapping for standard consensus values */
export declare const CONSENSUS_KEYS: Record<StandardConsensus, TranslationKey>;
/** Role values across all discussion methods */
export type RoleValue = "FOR" | "AGAINST" | "ADVOCATE" | "DEFENDER" | "QUESTIONER" | "RESPONDENT" | "PANELIST" | "IDEATOR" | "EVALUATOR";
/** Translation key mapping for role values */
export declare const ROLE_KEYS: Record<RoleValue, TranslationKey>;
/** Check if a string is a valid ConfidenceLevel */
export declare function isConfidenceLevel(value: string | undefined | null): value is ConfidenceLevel;
/** Check if a string is a valid StandardConsensus */
export declare function isStandardConsensus(value: string | undefined | null): value is StandardConsensus;
/** Check if a string is a valid RoleValue */
export declare function isRoleValue(value: string | undefined | null): value is RoleValue;
