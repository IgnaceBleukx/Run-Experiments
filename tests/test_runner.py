

import unittest
import tempfile
import os

import runexp


def make_lst(size_in_bytes):
    data = [0] * size_in_bytes # make a large list
    return dict(size_in_mb=size_in_bytes / (1024 * 1024), data=data)

def dummy(*args, **kwargs):
    return dict(result="None")

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
