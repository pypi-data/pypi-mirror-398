import {useState} from "react";
import {DEFAULT_THEME, MantineProvider} from "@mantine/core";

import type {TrainingProtocol} from "../models/trainingProtocol.ts";
import {sampleProtocol} from "../models/sampleData.ts";
import { TrainingProtocolContext } from "../hooks/useTrainingProtocol.ts";
import {App} from "./App.tsx"

export const AppContainer = () => {
    const [trainingProtocol, setTrainingProtocol] = useState<TrainingProtocol>(sampleProtocol);

    window.addEventListener("pywebviewready", () => {
        console.log("pywebviewready");
        window.pywebview.state.addEventListener("change", (event: CustomEvent) => {
            console.log(event);
            console.log("state changed:", window.pywebview.state.message1)
            console.log("state changed:", window.pywebview.state.message2)
            if (window.pywebview.state.protocol != null) {
                console.log(window.pywebview.state.protocol);
                setTrainingProtocol(window.pywebview.state.protocol);
            }
            const element = document.getElementById("counter");
            if (element !== null) {
                element.innerText = window.pywebview.state.message1
            }
        })
    });

    return (
        <MantineProvider theme={DEFAULT_THEME}>
            <TrainingProtocolContext.Provider value={trainingProtocol}>
                <App/>
            </TrainingProtocolContext.Provider>
        </MantineProvider>
    );
}