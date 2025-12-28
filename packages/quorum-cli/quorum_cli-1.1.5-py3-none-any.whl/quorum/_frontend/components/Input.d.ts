/**
 * Text input component with command palette integration.
 */
interface InputProps {
    value: string;
    onChange: (value: string) => void;
    onSubmit: (value: string) => void;
    onCommand: (command: string) => void;
    onHistoryNavigate?: (direction: "up" | "down") => void;
    onAdvisorOpen?: () => void;
    placeholder?: string;
    disabled?: boolean;
}
export declare function Input({ value, onChange, onSubmit, onCommand, onHistoryNavigate, onAdvisorOpen, placeholder, disabled, }: InputProps): import("react/jsx-runtime").JSX.Element;
export {};
