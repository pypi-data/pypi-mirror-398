import type {TrainingPhase} from "./trainingPhase.ts";

export type TrainingProtocol = {
    planId: string;
    name: string;
    description: string;

    phases: TrainingPhase[];
}
