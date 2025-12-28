import json
import numpy as np


class AnalysisConfig:
    def __init__(self):
        self.event_threshold = None
        self.hit_threshold = None

        self.layer_id = None
        self.max_per_layer = None
        self.max_total = None

    def _import(self, path):
        config = json.load(open(path, "r"))

        self.event_threshold = config["event_threshold"]
        self.hit_threshold = config["hit_threshold"]

        self.layer_id = np.array(config["layer_id"], dtype=np.int64)
        self.max_per_layer = np.array(config["max_per_layer"], dtype=np.int64)
        self.max_total = config["max_total"]


    def _export(self, path):
        config = {
            "event_threshold": self.event_threshold,
            "hit_threshold": self.hit_threshold,
            "layer_id": self.layer_id.tolist(),
            "max_per_layer": self.max_per_layer.tolist(),
            "max_total": self.max_total
        }
        json.dump(config, open(path, "w"), indent=4)


