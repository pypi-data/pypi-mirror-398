import numpy as np
import pandas as pd
import json


class MuTxtFormat:
    def __init__(self):
        self.data = None

        self.column = None
        self.dict_key = None
        self.bit_size = None
        self.dtype = None

        self.names = None

        self.cols = None
        self.dtypes = None

        self.sep = None
        self.header = None
        self.comment = None
        self.engine = None
        self.memory_map = None
        self.na_filter = None
        self.skip_blank_lines = None

        self.TCNT_bit_size = None
        self.PCNT_bit_size = None

    def _import(self, path):
        config = json.load(open(path, "r"))

        self.column = np.array(config["column"], dtype=np.int16)
        self.dict_key = np.array(config["dict_key"])
        self.bit_size = np.array(config["bit_size"], dtype=np.int16)
        self.dtype = np.array(config["dtype"])

        self.names = config["names"]

        self.cols = config["cols"]
        self.dtypes = {k: v for k, v in config["dtypes"].items()}

        self.sep = config["sep"]
        self.header = config["header"]
        self.comment = config["comment"]
        self.engine = config["engine"]
        self.memory_map = config["memory_map"]
        self.na_filter = config["na_filter"]
        self.skip_blank_lines = config["skip_blank_lines"]

        self.TCNT_bit_size = config["TCNT_bit_size"]
        self.PCNT_bit_size = config["PCNT_bit_size"]

    def _export(self, path):
        config = {
            "column": self.column.tolist(),
            "dict_key": self.dict_key.tolist(),
            "bit_size": self.bit_size.tolist(),
            "dtype": self.dtype.tolist(),
            "names": self.names,
            "cols": self.cols,
            "dtypes": {k: v for k, v in self.dtypes.items()},
            "sep": self.sep,
            "header": self.header,
            "comment": self.comment,
            "engine": self.engine,
            "memory_map": self.memory_map,
            "na_filter": self.na_filter,
            "skip_blank_lines": self.skip_blank_lines,
            "TCNT_bit_size": self.TCNT_bit_size,
            "PCNT_bit_size": self.PCNT_bit_size
        }
        json.dump(config, open(path, "w"), indent=4)

    def _generate(self, path):
        self.data = pd.read_csv(path, delimiter=",")

        self.column = self.data["column"].to_numpy(copy=False).astype(np.int16)
        self.dict_key = self.data["python dictionary key"].to_numpy(copy=False)
        self.bit_size = self.data["bit size"].to_numpy(copy=False).astype(np.int16)
        self.dtype = self.data["python dtype"].to_numpy(copy=False)

        self.names = ["BOARDID", "CHANNELID", "TIMESTAMP", "PCNT", "TCNT", "PWIDTH"]

        self.cols = []
        self.dtypes = {}

        self.sep = "\t"
        self.header = None
        self.comment = "#"
        self.engine = "c"
        self.memory_map = True
        self.na_filter = False
        self.skip_blank_lines = False

        for i in range(len(self.column)):
            if self.dict_key[i] in self.names:
                self.cols.append(int(self.column[i]))
                self.dtypes[self.dict_key[i]] = self.dtype[i]

        self.TCNT_bit_size = self.bit_size[self.dict_key == "TCNT"][0]
        self.PCNT_bit_size = self.bit_size[self.dict_key == "PCNT"][0]

