from .runexp import *

import argparse
from multiprocessing import cpu_count

def default_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("config", type=str, help="Configuration file, should be json-formatted")
    parser.add_argument("func", type=str, help="Main function of the experiment")
    parser.add_argument("runner", type=str, help="runexp Runner subclass to call")
    parser.add_argument("output", type=str, help="Directory to output results of experiments")
    parser.add_argument("-u", "--unravel", action="store_true", help="Whether to unravel config file to run experiments in a batch (will unravel lists in configuration file to separate configs)")
    parser.add_argument("--parallel", action="store_true", help="Wheter to run experiments in paralell, only useful if `--unravel` is True")
    parser.add_argument("--num-workers", action="store", type=int, default=cpu_count()-1, help=f"Number of threads to use for parallelization (=nb of experiments running in parallel, default={cpu_count()-1})")
    parser.add_argument("--memory_limit", action="store", type=int, default=-1, help="Memory limit in MB to use by each experiment, only works on Linux.")
    return parser