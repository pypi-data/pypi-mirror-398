/**
 * Floating command palette component.
 * Appears above the input when "/" is typed.
 */
interface CommandPaletteProps {
    filter: string;
    onSelect: (command: string, executeNow: boolean) => void;
    onClose: () => void;
}
export declare function CommandPalette({ filter, onSelect, onClose }: CommandPaletteProps): import("react/jsx-runtime").JSX.Element;
export {};
