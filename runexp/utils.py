import glob
import multiprocessing
from datetime import datetime, timedelta, date
from json import JSONDecodeError
from os.path import join
from os import listdir
import pickle
import json

import pandas as pd
from tqdm.auto import tqdm
from natsort import natsorted # pip install natsort

dirlock = multiprocessing.Lock()

CONFIG = "config.json"
STRFTIME = "%Y-%m-%d %H:%M:%S"

MAGIC_DT = "_dt" # which magic seqence a datetime value should end with
MAGIC_TD = "_td" # which magic seqence a timedelta value should end with

def can_stringify(val):
    return isinstance(val, (float, int, str))


###########################
#     Processing dicts    #
###########################

def unravel_dict(root_d, _dt=False, _td=False):
    new_dicts = [dict()]

    # range?
    if isinstance(root_d, dict) and {"_from", "_to"} <= set(root_d.keys()):
        if _dt is True:
            assert "_step" in root_d, f"Unraveling a datetime range requires a step-size: {root_d}"
            start = pd.to_datetime(root_d['_from'])
            end = pd.to_datetime(root_d['_to'])
            step = pd.to_timedelta(root_d['_step'])
            root_d = []
            t = start
            while t < end:
                root_d.append({"start": t, "delta": step})
                t += step
        elif _td is True:
            raise ValueError("Cannot make a range from time-delta's!", root_d)
        else: # normal range
            root_d = list(range(root_d['_from'], root_d['_to'], root_d.get("_step", 1)))


    if isinstance(root_d, dict):
        for key, val in root_d.items():
            if key.endswith(MAGIC_DT):
                sub_dicts = unravel_dict(val, _dt=True)
            elif key.endswith(MAGIC_TD):
                sub_dicts = unravel_dict(val, _td=True)
            else:
                sub_dicts = unravel_dict(val)
            new_dicts = [d | {key : sd} for sd in sub_dicts for d in new_dicts]

    elif isinstance(root_d, list):
        new_dicts = [unravel_dict(val) for val in root_d]
        new_dicts = [d for lst in new_dicts for d in lst]

    elif isinstance(root_d, str):
        if "*" in root_d: # filename, expand
            new_dicts = natsorted(glob.glob(root_d))
        elif _dt is True: # datetime, convert
            new_dicts = [pd.to_datetime(root_d)]
        elif _td is True: # time delta, convert
            new_dicts = [pd.to_timedelta(root_d)]
        else:
            new_dicts = [root_d]
    else:
        new_dicts = [root_d] # nothing to unravel

    return new_dicts

def flat_dict(d, separator="/"):
    assert isinstance(d, dict), f"Expected dictionary but got {type(d)}"
    flat = dict()
    for key, val in d.items():
        if isinstance(val, dict):
            flat_sub = flat_dict(val, separator)
            for subkey, subval in flat_sub.items():
                flat[f"{key}{separator}{subkey}"] = subval
        else:
            flat[key] = val
    return flat


def dict_subset(d1, d2):
    """
        Recursively check whether d1 is a subset of d2.
        A dictionary is a subset of another if it contains a subset of the keys, and matches each present value.
    """
    if type(d1) != type(d2):
        # check for datetime
        if isinstance(d1, datetime) or isinstance(d2, datetime):
            if isinstance(d1, datetime):
                d1 = d1.strftime(STRFTIME)
            if isinstance(d2, datetime):
                d2 = d2.strftime(STRFTIME)
            if d1 != d2:
                return False
        return False

    if not set(d1.keys()).issubset(set(d2.keys())):
        return False

    for key in d1:
        if isinstance(d1[key], dict):  # recurse
            if not dict_subset(d1[key], d2[key]):
                return False
        elif d1[key] != d2[key]:
            return False

    return True

###########################
#     Handling datetime   #
###########################
def dt_to_str_in_dict(d):

    if isinstance(d, datetime):
        return d.strftime(STRFTIME)
    elif isinstance(d, timedelta):
        return f"{d.total_seconds()} seconds"
    elif isinstance(d, list):
        return [dt_to_str_in_dict(x) for x in d]
    elif isinstance(d, set):
        return (dt_to_str_in_dict(x) for x in d)
    elif isinstance(d, dict):
        return {k : dt_to_str_in_dict(v) for k, v in d.items()}
    else:
        return d


###########################
#      Loading results    #
###########################
def results_to_df(dirname, fnames=[], separator="/", ignore_missing=False):
    dirs = sorted(listdir(dirname))
    pbar = tqdm(total=len(dirs), desc="Reading results from disk")
    missing = []
    data = []
    for edir in dirs:
        row = dict()
        for fname in [CONFIG] + fnames:
            fullname = join(dirname, edir, fname)
            attr = fname.split("/")[-1].split(".")[0]  # remove extension
            try:
                res = {attr: load_from_file(fullname)}
                row.update(flat_dict(res, separator))
            except FileNotFoundError as e:
                if ignore_missing is True:
                    missing.append(fullname)
                else:
                    raise e
        data.append(row)
        pbar.update()

    if len(missing):
        print(f"WARNING: missing following files:")
        for n in natsorted(missing):
            print(n)

    df = pd.DataFrame.from_dict(data)
    df.index = dirs
    return df


def load_from_file(fname) -> dict:
    attr = fname.split("/")[-1].split(".")[0] #remove extension

    if fname.endswith(".json"):
        try:
            with open(fname, "r") as f:
                return json.loads(f.read())
        except JSONDecodeError as e:
            print(f"Error while loading {fname}")
            raise e
    elif fname.endswith(".pickle"):
        with open(fname, "rb") as f:
            return {attr: pickle.loads(f.read())}
    elif fname.endswith(".txt"):
        with open(fname, "r") as f:
            str_val = f.read()
            try:
                return {attr: eval(str_val)}
            except (NameError, SyntaxError):
                return {attr : str_val}
    elif fname.endswith(".lst"):
        with open(fname, "r") as f:
            res = []
            for l in f.readlines():
                try:
                    res.append(eval(l.strip()))
                except NameError:
                    res.append(l.strip())
            return {attr : res}
    else:
        raise ValueError(f"Unknown file extension for file {fname}")





