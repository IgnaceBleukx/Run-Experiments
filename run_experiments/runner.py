

import argparse
import logging
import multiprocessing
import os

import sys
import time
import json
import pickle
import random
import datetime
import glob
import tqdm
import copy
from frozendict import frozendict

from .utils import dict_subset, unravel_dict, can_stringify

from os.path import dirname, abspath, join
from os import listdir


class Runner:

    def __init__(self, func, output=None, parallel=False, printlog=True, log_level=logging.INFO):

        if output is None:
            raise ValueError("No output dir was provided")

        try:
            os.mkdir(output)
        except FileExistsError:
            answer = input(f"Results directory {output} already exists, append results to this directory? (y/n)")
            if answer == "y":
                pass
            else:
                exit(1)

        self.func = func
        self.output_dir = output
        self.parallel = parallel
        self.digits = 6

        if printlog is True:
            logging.basicConfig(level=log_level,
                                format="%(asctime)s [%(levelname)s] %(message)s",
                                handlers=[logging.StreamHandler(sys.stdout)])
        else:
            raise NotImplementedError("Logging to file not yet implemented")
    def run_batch(self, config):

        configs = unravel_dict(config)

        self.n_experiments = len(configs)

        if self.parallel is True:
            n_workers = multiprocessing.cpu_count()
            pool = multiprocessing.Pool(n_workers - 1, maxtasksperchild=1)
            pool.map(self.run_experiment, configs)

        for config in configs:
            self.run_experiment(config)

    def make_kwargs(self, config):
        raise NotImplementedError(f"Implement `make_kwargs` for type {self}")


    def run_experiment(self, config):
        dirname = self.setup_experiment()
        try:
            kwargs = self.make_kwargs(config)
            result = self.func(**kwargs)
            self.save_result(config, result, dirname)
        except Exception as e:
            self.cleanup(dirname)
            raise e

    def cleanup(self, dirname):
        assert len(listdir(dirname)) == 0, "Directory must be empty!"
        os.rmdir(dirname)

    def setup_experiment(self):
        # make dir for results
        idx = len(listdir(self.output_dir))+1
        dirname = (self.digits - len(str(idx))) * "0" + str(idx)
        full_dir = join(self.output_dir, dirname)
        os.mkdir(full_dir)
        return full_dir

    def save_result(self,config, result, dirname):
        with open(join(dirname, "config.json"), "w") as f:
            f.write(json.dumps(config))

        for key, value in result.items():
            if can_stringify(value):
                with open(join(dirname, str(key)+".txt"), "w") as f:
                    f.write(str(value))

            if isinstance(value, dict):
                with open(join(dirname, str(key)+".json"),"w") as f:
                    f.write(json.dumps(value))

            if isinstance(value, list) and all(can_stringify(v) for v in value):
                with open(join(dirname, str(key)+".txt"),"w"):
                    f.write("\n".join(value))
            else: # save as pickle
                with open(join(dirname, str(key)+".pickle"), "wb") as f:
                    pickle.dump(value, f)