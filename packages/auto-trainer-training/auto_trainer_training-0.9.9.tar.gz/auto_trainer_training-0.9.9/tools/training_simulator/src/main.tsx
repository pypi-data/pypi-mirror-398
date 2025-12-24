import {StrictMode} from "react"
import {createRoot} from "react-dom/client"

import {AppContainer} from "./components/AppContainer.tsx";

import "@mantine/core/styles.css";
import "@mantine/dropzone/styles.css";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <AppContainer/>
    </StrictMode>
)
