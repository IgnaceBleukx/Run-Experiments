import glob
import multiprocessing

dirlock = multiprocessing.Lock()

def unravel_dict(root_d):
    new_dicts = [dict()]

    if isinstance(root_d, dict):
        for key, val in root_d.items():
            sub_dicts = unravel_dict(val)
            new_dicts = [d | {key : sd} for sd in sub_dicts for d in new_dicts]

    elif isinstance(root_d, list):
        new_dicts = [unravel_dict(val) for val in root_d]
        new_dicts = [d for lst in new_dicts for d in lst]

    elif isinstance(root_d, str) and "*" in root_d:
        new_dicts = glob.glob(root_d) # filename, expand
    else:
        new_dicts = [root_d] # nothing to unravel

    return new_dicts

def dict_subset(d1, d2):
    if type(d1) != type(d2):
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