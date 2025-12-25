/**
 * IPC Client for communicating with Quorum Python backend.
 */
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { EventEmitter } from "node:events";
import { v4 as uuidv4 } from "uuid";
export class BackendClient extends EventEmitter {
    process = null;
    readline = null;
    pendingRequests = new Map();
    isReady = false;
    readyPromise = null;
    readyResolve = null;
    pythonCommand;
    pythonArgs;
    constructor() {
        super();
        // Python tells us where it is via QUORUM_PYTHON env var (set by main.py)
        // This works for both dev mode and pip install
        this.pythonCommand = process.env.QUORUM_PYTHON || "python";
        this.pythonArgs = ["-m", "quorum", "--ipc"];
    }
    /**
     * Start the backend process.
     */
    async start() {
        if (this.process) {
            throw new Error("Backend already started");
        }
        this.readyPromise = new Promise((resolve) => {
            this.readyResolve = resolve;
        });
        this.process = spawn(this.pythonCommand, this.pythonArgs, {
            stdio: ["pipe", "pipe", "pipe"],
        });
        this.process.on("error", (err) => {
            this.emit("error", err);
        });
        this.process.on("exit", (code) => {
            this.isReady = false;
            this.emit("exit", code);
        });
        // Read stdout line by line
        if (this.process.stdout) {
            this.readline = createInterface({
                input: this.process.stdout,
                crlfDelay: Infinity,
            });
            this.readline.on("line", (line) => {
                this.handleLine(line);
            });
        }
        // Capture stderr for debugging
        if (this.process.stderr) {
            const stderrReader = createInterface({
                input: this.process.stderr,
                crlfDelay: Infinity,
            });
            stderrReader.on("line", (line) => {
                this.emit("stderr", line);
            });
        }
        // Wait for ready event
        await this.readyPromise;
    }
    /**
     * Stop the backend process.
     */
    stop() {
        if (this.readline) {
            this.readline.close();
            this.readline = null;
        }
        if (this.process) {
            this.process.kill();
            this.process = null;
        }
        this.isReady = false;
        // Reject all pending requests
        for (const [id, pending] of this.pendingRequests) {
            pending.reject(new Error("Backend stopped"));
        }
        this.pendingRequests.clear();
    }
    /**
     * Handle a line of output from the backend.
     */
    handleLine(line) {
        if (!line.trim())
            return;
        let message;
        try {
            message = JSON.parse(line);
        }
        catch (e) {
            this.emit("parse_error", line);
            return;
        }
        // Check if it's a response (has id) or notification
        if ("id" in message && message.id !== undefined) {
            const response = message;
            const pending = this.pendingRequests.get(String(response.id));
            if (pending) {
                this.pendingRequests.delete(String(response.id));
                if (response.error) {
                    pending.reject(new Error(response.error.message));
                }
                else {
                    pending.resolve(response.result);
                }
            }
        }
        else {
            // It's a notification/event
            const notification = message;
            const method = notification.method;
            // Handle ready event specially
            if (method === "ready" && this.readyResolve) {
                this.isReady = true;
                this.readyResolve();
                this.readyResolve = null;
            }
            // Emit the event
            this.emit(method, notification.params);
        }
    }
    /**
     * Send a request and wait for response.
     */
    async request(method, params = {}) {
        if (!this.process || !this.process.stdin) {
            throw new Error("Backend not started");
        }
        if (!this.isReady && method !== "initialize") {
            await this.readyPromise;
        }
        const id = uuidv4();
        const request = {
            jsonrpc: "2.0",
            id,
            method,
            params,
        };
        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, {
                resolve: resolve,
                reject,
            });
            const line = JSON.stringify(request) + "\n";
            this.process.stdin.write(line);
        });
    }
    // =========================================================================
    // Public API Methods
    // =========================================================================
    async initialize() {
        return this.request("initialize");
    }
    async listModels() {
        return this.request("list_models");
    }
    async validateModel(modelId) {
        return this.request("validate_model", { model_id: modelId });
    }
    async getConfig() {
        return this.request("get_config");
    }
    async getUserSettings() {
        return this.request("get_user_settings");
    }
    async saveUserSettings(settings) {
        await this.request("save_user_settings", settings);
    }
    async getInputHistory() {
        const result = await this.request("get_input_history");
        return result.history;
    }
    async addToInputHistory(input) {
        await this.request("add_to_input_history", { input });
    }
    async runDiscussion(params) {
        return this.request("run_discussion", params);
    }
    async cancelDiscussion() {
        await this.request("cancel_discussion");
    }
    async resumeDiscussion() {
        await this.request("resume_discussion");
    }
    async getRoleAssignments(method, modelIds) {
        const result = await this.request("get_role_assignments", {
            method,
            model_ids: modelIds,
        });
        return result.assignments;
    }
    async swapRoleAssignments(assignments) {
        const result = await this.request("swap_role_assignments", {
            assignments,
        });
        return result.assignments;
    }
    async analyzeQuestion(question) {
        return this.request("analyze_question", { question });
    }
    // =========================================================================
    // Typed Event Listeners
    // =========================================================================
    onEvent(event, listener) {
        return this.on(event, listener);
    }
    offEvent(event, listener) {
        return this.off(event, listener);
    }
}
