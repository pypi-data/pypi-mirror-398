export const sampleProtocol = {
    "planId": "57094295-5234-44f3-a925-14ceb772c8e5",
    "name": "Sample Training Protocol",
    "description": "A sample training protocol with multiple phases.",
    "phases": [
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Reach A",
            "description": "Manual pellet delivery (uncovered).",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [],
            "startingBaselineIntensity": 0,
            "isPelletCoverEnabled": false,
            "isAutoClampEnabled": false
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Reach B",
            "description": "Automated pellet delivery (uncovered).",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [],
            "startingBaselineIntensity": 0,
            "isPelletCoverEnabled": false,
            "isAutoClampEnabled": false
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Reach C",
            "description": "Pellet positioning to maximum distance (covered with reach distance).",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [
                {
                    "type": "ReachDistanceAction",
                    "module": "autotrainer.training.training_action",
                    "properties": {
                        "distance": 3.0,
                        "increment": 0.5,
                        "pellet_delta": 5
                    }
                }
            ],
            "startingBaselineIntensity": 0,
            "isPelletCoverEnabled": true,
            "isAutoClampEnabled": false
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Reach D",
            "description": "Stable automatic delivery (covered with reach distance).",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [],
            "startingBaselineIntensity": 10,
            "isPelletCoverEnabled": true,
            "isAutoClampEnabled": false
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Head Fix A",
            "description": "Magnet baseline incremental training",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [
                {
                    "type": "HeadMagnetIntensityAction",
                    "module": "autotrainer.training.training_action",
                    "properties": {
                        "start": 0.0,
                        "increment": 10,
                        "end": 90,
                        "pellet_delta": 5
                    }
                }
            ],
            "startingBaselineIntensity": 0,
            "isPelletCoverEnabled": true,
            "isAutoClampEnabled": false
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Head Fix B",
            "description": "90% Magnet baseline without auto-clamp",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [],
            "isPelletDeliveryEnabled": true,
            "isPelletCoverEnabled": true,
            "startingBaselineIntensity": 90,
            "pelletHandsMinDistance": 3.2,
            "isPelletShiftEnabled": false,
            "isAutoClampEnabled": false,
            "autoClampNoActivityReleaseDelay": 5.0,
            "autoClampReleaseLoadCount": 3
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Head Fix C",
            "description": "Auto-clamp enabled.  Deliver pellets until a pellet remains in the at-mouse position for [x] seconds, then release the mouse (tone, then release).",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [],
            "startingBaselineIntensity": 90,
            "isPelletCoverEnabled": true,
            "isAutoClampEnabled": true
        },
        {
            "phaseId": "3a37f67e-12f1-47e3-ae9a-fd6d0edb9bac",
            "name": "Head Fix D",
            "description": "Auto-clamp enabled until digital feed indicates release.",
            "fallbackPredicate": null,
            "advancePredicate": {
                "type": "NumberComparisonPredicate",
                "module": "autotrainer.training.training_predicate",
                "properties": {
                    "comparisonType": "GTE",
                    "path": [
                        "progress",
                        "pellets_consumed"
                    ],
                    "value": 3
                }
            },
            "sessionActions": [],
            "startingBaselineIntensity": 90,
            "isPelletCoverEnabled": true,
            "isAutoClampEnabled": true
        }
    ]
};

export const sampleProgress = {
  "plan_id": "57094295-5234-44f3-a925-14ceb772c8e5",
  "progress_state": 10,
  "current_phase_id": "phase-1-uuid-67890",
  "progress": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "timeInTraining": 3600.5,
      "sessionCount": 5,
      "pelletsConsumed": 12,
      "pelletStartLocation": [
        1.0,
        2.0,
        3.0
      ],
      "pelletCurrentLocation": [
        1.1,
        2.1,
        3.1
      ],
      "successfulReaches": 8,
      "phaseAttempts": 3,
      "userContext": {
        "notes": "Good progress",
        "difficulty": "easy"
      }
    },
    {
      "timestamp": "2024-01-16T11:15:00",
      "timeInTraining": 1800.0,
      "sessionCount": 3,
      "pelletsConsumed": 6,
      "pelletStartLocation": [
        2.0,
        3.0,
        4.0
      ],
      "pelletCurrentLocation": [
        2.2,
        3.2,
        4.2
      ],
      "successfulReaches": 4,
      "phaseAttempts": 1,
      "userContext": {}
    },
    {
      "timestamp": "2024-01-17T09:00:00",
      "timeInTraining": 900.0,
      "sessionCount": 1,
      "pelletsConsumed": 2,
      "pelletStartLocation": [
        3.0,
        4.0,
        5.0
      ],
      "pelletCurrentLocation": [
        3.0,
        4.0,
        5.0
      ],
      "successfulReaches": 2,
      "phaseAttempts": 1,
      "userContext": {
        "notes": "Just started"
      }
    }
  ]
};
