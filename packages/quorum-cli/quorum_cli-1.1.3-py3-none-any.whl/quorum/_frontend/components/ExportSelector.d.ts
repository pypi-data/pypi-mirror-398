/**
 * Export selector for choosing which discussion to export.
 * Shows the 10 most recent discussions with navigation.
 */
import { type ExportFormat } from "../utils/export.js";
interface ExportSelectorProps {
    reportDir: string;
    format: ExportFormat;
    onExport: (reportPath: string) => void;
    onCancel: () => void;
}
export declare function ExportSelector({ reportDir, format, onExport, onCancel }: ExportSelectorProps): import("react/jsx-runtime").JSX.Element;
export {};
