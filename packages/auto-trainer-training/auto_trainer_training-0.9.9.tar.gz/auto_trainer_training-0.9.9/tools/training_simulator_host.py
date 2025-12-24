import json
import logging
from pathlib import Path
from typing import Optional

import webview
from webview import Window

from autotrainer.training.training_simulator import TrainingSimulator

logger = logging.getLogger(__name__)

window: Optional[Window] = None


class Api:
    def __init__(self):
        self.window = None
        self.simulator: TrainingSimulator = TrainingSimulator()
        self.idx = 0

    def log(self, message):
        print(message)
        logger.info(message)
        if window is not None:
            print("window")
            if self.idx % 2 == 0:
                window.state.message1 = message
            else:
                window.state.message2 = message
            self.idx += 1

    def load_protocol(self, path: str, contents: str):
        window.state.protocol = None
        print("ok")
        data = json.loads(contents)
        self.simulator.load_training_plan_data(path, data)
        window.state.protocol = self.simulator.training_plan.to_dict()

    def increase_pellets_consumed(self, amount: int):
        self.simulator.increase_pellets_consumed(amount)


def training_simulator_main():
    global window

    api = Api()

    window = webview.create_window("Training Simulator", "training_simulator/dist/index.html", js_api=api,
                                   min_size=(800, 800))

    webview.start(debug=True)


if __name__ == "__main__":
    training_simulator_main()
