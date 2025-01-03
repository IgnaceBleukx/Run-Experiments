from runexp import Runner, default_parser

# make sure everything you call is imported here
from data_wrappers import HandyDataWrapper

class MyRunner(Runner):

    def description(self, config):
        return f"Handling seed {config['seed']}"

    def make_kwargs(self, config):

        output = dict()

        for key, val in config.items():
            if key == "arg1":
                cname = val['name']
                # instantiate class
                output['arg1'] = eval(cname)(val['v1'], val['v2'])
            else:
                output[key] = val

        return output



if __name__ == "__main__":

    from experiment import my_cool_experiment # make sure `func` is imported here
    import json

    parser = default_parser()

    args = parser.parse_args()
    with open(args.config, "r") as f:
        config = json.loads(f.read())
        runner = eval(args.runner)(func=eval(args.func),
                                   output=args.output,
                                   memory_limit=args.memory_limit,
                                   printlog=True)

        if args.unravel is True:
            runner.run_batch(config, parallel=args.parallel, num_workers=args.num_workers)
        else:
            runner.run_one(config)
