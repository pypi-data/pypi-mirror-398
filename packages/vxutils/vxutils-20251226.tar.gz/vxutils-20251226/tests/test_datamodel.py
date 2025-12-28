import unittest
import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
if "vxutils" in sys.modules:
    del sys.modules["vxutils"]
import datetime
import time
from typing import Optional
from pydantic import Field, PlainValidator

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from vxutils.datamodel.core import VXDataModel
from vxutils.convertors import to_datetime, to_json


class Tick(VXDataModel):
    symbol: str
    trigger_dt: Annotated[datetime.datetime, PlainValidator(to_datetime)] = Field(
        default_factory=datetime.datetime.now
    )


class TestVXDataModel(unittest.TestCase):
    def test_defaults_and_type_conversion(self):
        m = Tick(symbol="000001")
        self.assertIsInstance(m.created_dt, datetime.datetime)
        self.assertIsInstance(m.updated_dt, datetime.datetime)
        self.assertEqual(m.created_dt, m.updated_dt)

        before = m.updated_dt
        time.sleep(0.01)
        m.symbol = "000002"
        self.assertGreaterEqual(m.updated_dt, before)
        self.assertNotEqual(m.updated_dt, before)

        m.trigger_dt = "2021-01-01 00:00:00"
        self.assertIsInstance(m.trigger_dt, datetime.datetime)

    def test_getitem_and_json(self):
        m = Tick(symbol="abc")
        self.assertEqual(m["symbol"], "abc")
        js = to_json(m)
        self.assertIn("symbol", js)


if __name__ == "__main__":
    unittest.main()
