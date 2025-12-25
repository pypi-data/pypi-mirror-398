/**
 * JSON-RPC 2.0 protocol types for Quorum IPC.
 */
// ============================================================================
// Protocol Version
// ============================================================================
/**
 * Protocol version for frontend-backend compatibility.
 * Increment MAJOR for breaking changes, MINOR for additions, PATCH for fixes.
 * Backend checks this to warn about compatibility issues.
 */
export const PROTOCOL_VERSION = "1.0.0";
