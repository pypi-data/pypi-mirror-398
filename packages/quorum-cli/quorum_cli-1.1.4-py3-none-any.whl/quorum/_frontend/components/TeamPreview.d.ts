/**
 * Team assignment preview for Oxford/Advocate/Socratic modes.
 * Shows role assignments before debate starts and allows customization.
 */
import type { RoleAssignments } from "../ipc/protocol.js";
import { DiscussionMethod } from "../store/index.js";
interface TeamPreviewProps {
    assignments: RoleAssignments;
    method: DiscussionMethod;
    onConfirm: (assignments: RoleAssignments) => void;
    onCancel: () => void;
}
export declare function TeamPreview({ assignments, method, onConfirm, onCancel }: TeamPreviewProps): import("react/jsx-runtime").JSX.Element;
export {};
