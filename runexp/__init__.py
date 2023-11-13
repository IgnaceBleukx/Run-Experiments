from .runexp import *

import argparse
from multiprocessing import cpu_count

def default_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("config", type=str, help="Configuration file, should be json-formatted")
    parser.add_argument("func", type=str, help="Main function of the experiment")
    parser.add_argument("runner", type=str, help="runexp Runner subclass to call")
    parser.add_argument("output", type=str, help="Directory to output results of experiments")
    parser.add_argument("--batch", type=bool, default=True, help="Whether to run experiments in a batch (will unravel lists in configuration file to separate configs)")
    parser.add_argument("--parallel", type=bool, default=False, help="Wheter to run experiments in paralell, only useful if `--batch` is True")
    parser.add_argument("--num-workers", type=int, default=cpu_count()-1, help="Number of threads to use for parallelization (=nb of experiments running in parallel, default=numthreads-1)")

    return parser


def run(parser:argparse.ArgumentParser):

    import importlib
    import traceback

    called_from = traceback.extract_stack(limit=2)[-1]
    print(called_from.filename)
    # importlib.import_module(called_from.filename)
    # importlib.__import__(called_from.filename)


    args = parser.parse_args()
    eval(f"from {called_from.filename} import {eval(args.runner)}")


    with open(args.config, "r") as f:
        config = json.loads(f.read())
        runner = eval(args.runner)(func=eval(args.func),
                                   output=args.output,
                                   printlog=False)

        if args.batch is True:
            runner.run_batch(config, parallel=args.parallel, num_workers=args.num_workers)
        else:
            runner.run_one(config)