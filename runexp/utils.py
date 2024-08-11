import glob
import multiprocessing
import time
from datetime import datetime, timedelta, date
from json import JSONDecodeError
from os.path import join
from os import listdir
import pickle
import json

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from natsort import natsorted # pip install natsort


dirlock = multiprocessing.Lock()

CONFIG = "config.json"
STRFTIME = "%Y-%m-%d %H:%M:%S"

def unravel_dict(root_d):
    new_dicts = [dict()]

    # range?
    if isinstance(root_d, dict) and {"_from", "_to"} <= set(root_d.keys()):
        try:
            start = datetime.strptime(root_d["_from"], STRFTIME)
            stop = datetime.strptime(root_d["_to"], STRFTIME)
            step = root_d["_step"]
            units = ["seconds", "minutes", "hours", "days", "weeks", "months", "years"]
            for u in units:
                if u in step:
                    val, unit = step.split(" ")
                    assert unit == u
                    step = timedelta(**{unit : int(val)})
                    break
            if isinstance(step, str):
                raise NotImplementedError(f"Unknown time delta: {step}, chose from {units}")

            t = start
            root_d = []
            while t < stop:
                root_d.append({"start" : t, "stop": t+step})
                t += step

        except (TypeError, ValueError):
            root_d = list(range(root_d['_from'], root_d['_to'], root_d.get("_step", 1)))

    if isinstance(root_d, dict):
        for key, val in root_d.items():
            sub_dicts = unravel_dict(val)
            new_dicts = [d | {key : sd} for sd in sub_dicts for d in new_dicts]

    elif isinstance(root_d, list):
        new_dicts = [unravel_dict(val) for val in root_d]
        new_dicts = [d for lst in new_dicts for d in lst]

    elif isinstance(root_d, str) and "*" in root_d:
        new_dicts = natsorted(glob.glob(root_d)) # filename, expand
    else:
        new_dicts = [root_d] # nothing to unravel

    return new_dicts

def dict_subset(d1, d2):

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
        if isinstance(d1[key], dict):
            # recurse
            if not dict_subset(d1[key], d2[key]):
                return False
        elif d1[key] != d2[key]:
            return False

    return True


def dt_to_str_in_dict(d):

    if isinstance(d, datetime):
        return d.strftime(STRFTIME)

    elif isinstance(d, list):
        return [dt_to_str_in_dict(x) for x in d]

    elif isinstance(d, set):
        return (dt_to_str_in_dict(x) for x in d)

    elif isinstance(d, dict):
        return {k : dt_to_str_in_dict(v) for k, v in d.items()}
    else:
        return d

def get_flat_dict(d):
    new_dict = dict()
    for key, val in d.items():
        if isinstance(val, dict):
            for subkey, subval in get_flat_dict(val).items():
                new_dict[(key,) + subkey] = subval
        else:
            new_dict[(key,)] = val
    return new_dict


def can_stringify(val):
    return isinstance(val, (float, int, str))


def load_from_file(fname) -> dict:
    # print(f"Loading {fname}")
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
        with open(fname, "rb") as f:
            return {attr: eval(f.read())}
    elif fname.endswith(".lst"):
        with open(fname, "r") as f:
            return {attr: [eval(l.strip()) for l in f.readlines()]}
    else:
        raise ValueError(f"Unknown file extension for file {fname}")

def results_to_df_old(dirname, fnames=[], separator="/", ignore_missing=False):
    dfs = []
    dirs = sorted(listdir(dirname))
    dirs_read = []
    pbar = tqdm(total=len(dirs), desc="Reading results from disk")
    missing = []
    for idx, fname in enumerate([CONFIG] + fnames):
        results_fname = []
        for edir in dirs:
            if listdir(join(dirname, edir)):
                fullname = join(dirname, edir, fname)
                try:
                    res = load_from_file(fullname)
                    results_fname.append(flat_dict(res, separator))
                    pbar.update(1/(1+len(fnames)))
                    if idx == 0: dirs_read.append(edir)
                except FileNotFoundError as e:
                    if ignore_missing:
                        missing.append(fullname)
                        results_fname.append(np.nan)
                    else:
                        raise e
        dfs.append(pd.DataFrame(results_fname))

    if len(missing):
        print(f"WARNING: missing following files:")
        for n in natsorted(missing):
            print(n)
    df = pd.concat(dfs, axis="columns")
    df.index = dirs_read
    return df


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

def load_results(dirname, attribute, filter=dict()):
    """
     load results from directory, filter based in filtering dict
    :param dirname: main directory of results
    :param attribute: artifact to load (any of the files stored)
    :param filter - optional: dictionary to filter configuration files
    :return:
    """
    assert isinstance(attribute, str)
    assert attribute.endswith(".txt") or \
            attribute.endswith(".json") or \
                attribute.endswith(".pickle"), "Please provide filename extension of the attribute"


    for edir in listdir(dirname):
        if CONFIG not in listdir(join(dirname, edir)):
            continue

        with open(CONFIG, "r") as f:
            config = json.loads(f.read())

        if dict_subset(filter, config) is False:
            continue

        fname = join(dirname, edir, attribute)
        if attribute.endswith(".json"):
            with open(fname, "r") as f:
                yield json.loads(f.read())
        elif attribute.endswith(".pickle"):
            with open(fname, "rb") as f:
                yield pickle.loads(f.read())
        else:
            with open(fname, "r") as f:
                yield eval(f.read())





