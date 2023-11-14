# RunExp

This repostory aims to be a collection of tools to ease running experiments.
Highlight features include:
- Clear filestructure
  - Including support for json and pickle files
- Easy paralellization of experiments
- Data loading tools for processing experiment results
- ...


## How to install?
The easiest way to use the repository is to download/clone the repo and install the package in "editable" mode:
```batch
$ pip install -e runexp
```

## How to use?
To use the `runexp` framework for running your experiments, you will need the following:

 - A main experiment function to call
 - A config file defining parameters and values for the above function
 - A subclass of the `Runner` class defining mapping from string-arguments to Python objects
 - A output directory to store results of your experiments

For each experiment, `runexp` will create a new directory in the `results` directory containing all artifacts of you experiment.

Below, we go into detail of each of the components by using the `example/...` folder as a running example

To run the example, run the following commands:

```batch
$ cd example
$ python3 main.py sample_config.json my_cool_experiment MyRunner results/FirstExperiment --unravel --parallel
```
The above example requires some argument parsing from the command line.
A default parser can be imported: `from runexp import default_parser`.
This parser will use the `argparse` library to parse some frequently used arguments.


### Experiment function
The main function of your experiment should take as input parameters defined in your configuration file.
The output of this function should be a dictionary. 
Each of the keys in this dictionary will be the filename of the artifact of the experiment.
Based on the type of artifact, the way `runexp` stores the value will be different:
1) If the artifact is human-readable (i.e., if it is a integer/string) the value will be put in a `.txt` file.
2) If the artifact is a dictionary containing only human-readable values, the artifact will be written as a `.json` file.
3) In all other cases, the value will be "pickled" and stored as a binary `.pickle` file.

For an example experiment function, take a look at the `example/experiment.py` file.
This experiment takes as input a data wrapper and a string.
The output of the experiment is an instance of a `HandyDataWrapper` object and a randomly shuffled version of the string it got as input argument.

### Config file
`runexp` uses `.json` based configuration files to define the parameters for your experiments.

If the optional argument `unravel` is set when calling `runexp`, the configuration file will be unraveled, essentially creating a batch of experiments.
I.e., if any of the values in the configuration file is a list, the contents of the remaining configuration will be replicated ones for each of the values in the list.
In `example/sample_config.json` this feature is used for `v2` of `arg1`.

`runexp` also allows you to define a range of values in the configuration file by using the special keys `_from` and `_to`.
This is identical to using `range(_from, _to)` in Python.
In `example/sample_config.json` this feature is highlighted in the `seed` parameter.

When the `--unravel` argument is set, the `sample_config.json` will be unraveled to 10 configuration files for running 10 experiments.

### Runner subclass
The `Runner` class is the heart of `runexp` where the magic happens.
In order to tailor the repository to work with your experiment, it suffices to fill in the `make_kwargs` function.
This function will take as input one (unraveled) configuration as a dictionary and aims to map the string-based arguments to actual Python objects.
The output of this function should be a dictionary containing all arguments to the `Experiment function` as keys.

In `example/main.py` you can find an example `Runner` class converting `arg1` in the configuration to a `HandyDataWrapper` instance.
Note that the JSON library used for loading configuration files automatically interprets strings, floats and ints from the json file.

#### Optional for pretty progress
`runexp` uses the `tqdm` library to track progress of your experiments.
To get some detailed information, you can override the `description(config)` function to return a more informative description of the experiment that is currently running.
Examples the particular problem instance you are running an experiment with in combination with a random seed.

### Output directory
`runexp` will create a results directory for each finished expeirment within the `output_dir`.
If `output_dir` already exists and contains some finished experiments already, `runexp` will scan those results and check if there is overlap with the currently planned experiments.
When this is the case, the already ran experiments will be skipped and not executed again.

The names given to each exeriment folder is a integer with leading zeros. The default setting uses 6 digits, allowing for 999.999 experiments in one folder.
This can be changed by setting the `digits` attribute in your `Runner` instance.

## Processing results

After running the experiments, `runexp` provides some utility function to ease the loading of results.
In particular, the `utils.load_results` function is interesting.
It takes as argument a main directory name (the parent dir of all `0000001`, `0000002`,... files) and the attribute to load.
Optionally, it also takes as argument a filter which is a dictionary that filters which experiments to load.
For example, if you would only like to load scrambled text of the results of the sample experiment, but only those who have `v2` to `1337`, you can use the following code:

```python3
from runexp.utils import load_results

filter = {"arg1": {"v2":1337}}
list(load_results("results/FirstExperiment", "scrambled_text", filter=filter))
```

# FAQ

I get the following error:

```
NameError: name 'my_cool_experiment' is not defined
```
**Fix**: Make sure `my_cool_experiment` is imported where the `Runner` instance is initialized. 