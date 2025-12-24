import {createContext, useContext} from "react";

import type {TrainingProtocol} from "../models/trainingProtocol.ts";

// @ts-expect-error This is ok
export const TrainingProtocolContext = createContext<TrainingProtocol>(null);

export const useTrainingProtocol = () => useContext(TrainingProtocolContext);