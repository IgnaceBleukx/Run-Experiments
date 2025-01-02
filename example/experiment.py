from data_wrappers import HandyDataWrapper
import random

def my_cool_experiment(arg1, arg2, seed=0):

    random.seed(seed)

    assert isinstance(arg1, HandyDataWrapper), f"expected HandyDataWrapper but got {type(arg1)}"
    assert isinstance(arg2, str)
    lst_arg2 = [letter for letter in arg2]
    random.shuffle(lst_arg2)

    return {
        "data_wrapper": arg1,
        "scrambled_text": "".join(lst_arg2)
    }