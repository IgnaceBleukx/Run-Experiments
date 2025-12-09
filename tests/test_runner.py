

import unittest
import tempfile
import os

import runexp


def make_lst(size_in_bytes):
    data = [0] * size_in_bytes # make a large list
    return dict(size_in_mb=size_in_bytes / (1024 * 1024), data=data)

def dummy(*args, **kwargs):
    return dict(result="None")

class Hashable:
    def __hash__(self): return 1
    def __eq__(self, other): return True


class RunnerTests(unittest.TestCase):

    class MyRunner(runexp.Runner):
        def make_kwargs(self, config): return config
        def description(self, config): return str(config)


    def test_one(self):
        tempdir = os.path.join(tempfile.mkdtemp(), "results")
        runner = self.MyRunner(dummy, output=tempdir)
        runner.run_one(config=dict(key1="val1", key2="val2", key_lst=[1,2,3]))
        self.assertEqual(len(os.listdir(tempdir)), 1)

    def test_batch(self):
        tempdir = os.path.join(tempfile.mkdtemp(), "results")
        runner = self.MyRunner(dummy, output=tempdir)
        runner.run_batch(config=dict(key1="val1", key2="val2", key_lst=[1, 2, 3]))
        self.assertEqual(len(os.listdir(tempdir)), 3)

    def test_batch_parallel(self):
        tempdir = os.path.join(tempfile.mkdtemp(), "results")
        runner = self.MyRunner(dummy, output=tempdir)
        runner.run_batch(config=dict(key1="val1", key2="val2", key_lst=[1, 2, 3]), parallel=True)
        self.assertEqual(len(os.listdir(tempdir)), 3)

    def test_memlimit(self):
        tempdir = os.path.join(tempfile.mkdtemp(), "results")
        runner = self.MyRunner(make_lst, output=tempdir, memory_limit=1024) # 1GB limit
        runner.run_batch(config=dict(size_in_bytes=[1024 ** x for x in range(5)]))

        self.assertIn("size_in_mb.txt", os.listdir(os.path.join(tempdir,"000001")))  # 1 byte should work
        self.assertIn("size_in_mb.txt", os.listdir(os.path.join(tempdir, "000002"))) # 1KB should work
        self.assertIn("size_in_mb.txt", os.listdir(os.path.join(tempdir, "000003"))) # 1MB should work
        self.assertIn("err.txt", os.listdir(os.path.join(tempdir, "000004")))        # 1GB should not work
        self.assertIn("err.txt", os.listdir(os.path.join(tempdir, "000005")))        # 10GB should not work


    def test_write_result(self):

        tempdir = "test_writing"
        #tempdir = os.path.join(tempfile.mkdtemp(), "results")
        runner = self.MyRunner(dummy, output=tempdir)


        adict = dict(val1 = "foo", val2 = "bar")
        bdict = dict(val1 = Hashable(), val2 = "bar")
        cdict = {Hashable() : "foo", "val2" : "bar"}

        result = {
                "result_txt": 'foo',
                "result_int": 42,
                "result_float": 13.37,
                "result_dict": adict,
                "result_bdict": bdict,
                "result_cdict": cdict,
                "result_pickle": Hashable()
                }

        runner.save_result(dict(origin="test_runner.py", func="test_write_result"), result, tempdir)

        # check results
        import pickle
        with open(os.path.join(tempdir, "result_txt.txt"),"r") as f:
            self.assertEqual(f.read(), "foo")
        with open(os.path.join(tempdir, "result_int.txt"), "r") as f:
            self.assertEqual(f.read(), "42")
        with open(os.path.join(tempdir, "result_float.txt"), "r") as f:
            self.assertEqual(f.read(), "13.37")
        with open(os.path.join(tempdir, "result_dict.json"), "r") as f:
            self.assertEqual(f.read(), '{"val1": "foo", "val2": "bar"}')
        with open(os.path.join(tempdir, "result_bdict.pickle"), "rb") as f:
            self.assertEqual(pickle.loads(f.read()), bdict)
        with open(os.path.join(tempdir, "result_cdict.pickle"), "rb") as f:
            self.assertEqual(pickle.loads(f.read()), cdict)
        with open(os.path.join(tempdir, "result_pickle.pickle"), "rb") as f:
            self.assertEqual(pickle.loads(f.read()), Hashable())

