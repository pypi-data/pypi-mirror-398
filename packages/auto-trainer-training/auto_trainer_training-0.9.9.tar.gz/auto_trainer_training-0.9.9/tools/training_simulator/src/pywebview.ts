import type {TrainingProtocol} from "./models/trainingProtocol.ts";

interface PythonAPI {
    log(message: string): void;

    load_protocol(name: string, contents: string): void;

    increase_pellets_consumed(amount: number): void;
}

type EventCallback = (event: CustomEvent) => void;

export type PythonState = {
    message1: string;
    message2: string;
    protocol: TrainingProtocol;

    addEventListener(name: string, listener: EventCallback): void;
}

declare global {
    interface Window {
        pywebview: {
            api: PythonAPI; // Or define a more specific interface for your exposed Python functions
            // Add other pywebview properties if you use them, e.g., 'platform'
            state: PythonState;
        };
    }
}

export function Log(message: string) {
    window.pywebview.api.log(message);
}

export function LoadProtocol(path: string, contents: string) {
    console.log(window.pywebview)
    window.pywebview.api.load_protocol(path, contents);
}
