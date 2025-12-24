export type TrainingPhase = {
    phaseId: string;
    name: string;
    description: string;

    isPelletDeliveryEnabled?: boolean;
    isPelletCoverEnabled?: boolean;
    startingBaselineIntensity?: number;
    pelletHandsMinDistance?: number;
    isPelletShiftEnabled?: boolean;
    isAutoClampEnabled?: boolean;
    autoClampNoActivityReleaseDelay?: number;
    autoClampReleaseLoadCount?: number;

    fallbackPredicate: any;
    advancePredicate: any;
    sessionActions: any[];
}