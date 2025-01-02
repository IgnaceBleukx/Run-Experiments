
import unittest

import pandas as pd

from runexp import unravel_dict
from runexp.utils import flat_dict


class TestDictUtils(unittest.TestCase):


    def test_unravel(self):
        config = dict(
            a1 = "v1",
            a2 = dict(a21="v21", a22="v22", a23=['v23_a', 'v23_b', 'v23_c']),
            a3 = ['v3_a', 'v3_b']
        )

        dicts = unravel_dict(config)
        self.assertEqual(len(dicts), 6)

    def test_unravel_range(self):
        config = dict(
            a1="v1",
            a2=dict(a21="v21", a22="v22", a23=dict(_from=0, _to=10, _step=3)),
            a3=dict(_from=1, _to=3)
        )
        dicts = unravel_dict(config)
        self.assertEqual(len(dicts), 8)

    def test_unravel_dt(self):
        config = dict(
            a1="v1",
            a2=dict(a21="v21", a22="v22"),
            start_dt="2024-01-01 00:00:00",
            end_dt="2024-01-01 01:00:00",
            delta_td = "10 seconds"
        )
        dicts = unravel_dict(config)
        self.assertEqual(len(dicts), 1)
        d = dicts[0]
        self.assertIsInstance(d['start_dt'], pd.Timestamp)
        self.assertIsInstance(d['end_dt'], pd.Timestamp)
        self.assertIsInstance(d['delta_td'], pd.Timedelta)



    def test_unravel_dt_range(self):
        config = dict(
            a1="v1",
            a2=dict(a21="v21", a22="v22", a23_dt=dict(_from="2025-01-01",
                                                      _to="2025-01-02",
                                                      _step="8 hours")),
            a3_dt=dict(_from="2024-01-01 00:00:00", _to="2024-01-01 01:00:15", _step="15 min")
        )
        dicts = unravel_dict(config)
        self.assertEqual(len(dicts), 15)


    def test_flatten(self):
        config = dict(
            a1="v1",
            a2=dict(a21="v21", a22="v22", a23='v23'),
            a3=dict(a31=dict(a311="v311", a312="v312")),
        )

        flat = flat_dict(config)
        self.assertDictEqual(flat,
                             {'a1': 'v1', 'a2/a21': 'v21', 'a2/a22': 'v22', 'a2/a23': 'v23', 'a3/a31/a311': 'v311', 'a3/a31/a312': 'v312'}
        )

        flat = flat_dict(config, separator="$")
        self.assertDictEqual(flat,
                             {'a1': 'v1', 'a2$a21': 'v21', 'a2$a22': 'v22', 'a2$a23': 'v23', 'a3$a31$a311': 'v311', 'a3$a31$a312': 'v312'}
        )