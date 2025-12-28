# tests/test_convertors.py
import unittest
import datetime
import time
from vxutils.convertors import to_timestr


class TestToTimestr(unittest.TestCase):
    """测试to_timestr函数"""

    def test_int_timestamp(self):
        """测试整数时间戳"""
        self.assertEqual(to_timestr(1609459200), "2021-01-01 00:00:00")
        self.assertEqual(to_timestr(1609459200, "%Y-%m-%d"), "2021-01-01")

    def test_float_timestamp(self):
        """测试浮点数时间戳"""
        self.assertEqual(to_timestr(1609459200.0), "2021-01-01 00:00:00")
        self.assertEqual(to_timestr(1609459200.5), "2021-01-01 00:00:00")

    def test_date_string(self):
        """测试日期字符串"""
        self.assertEqual(to_timestr("2021-01-01"), "2021-01-01 00:00:00")
        self.assertEqual(to_timestr("2021-01-01 12:30:45"), "2021-01-01 12:30:45")
        self.assertEqual(to_timestr("01/01/2021", "%Y-%m-%d"), "2021-01-01")

    def test_datetime_date(self):
        """测试datetime.date类型"""
        date_obj = datetime.date(2021, 1, 1)
        self.assertEqual(to_timestr(date_obj), "2021-01-01 00:00:00")

    def test_datetime_time(self):
        """测试datetime.time类型"""
        time_obj = datetime.time(12, 30, 45)
        self.assertEqual(to_timestr(time_obj, "%H:%M:%S"), "12:30:45")

    def test_struct_time(self):
        """测试time.struct_time类型"""
        struct_time = time.struct_time((2021, 1, 1, 0, 0, 0, 0, 0, 0))
        self.assertEqual(to_timestr(struct_time), "2021-01-01 00:00:00")

    def test_invalid_input(self):
        """测试无效输入"""
        with self.assertRaises(ValueError):
            to_timestr("invalid date string")
        with self.assertRaises(ValueError):
            to_timestr(None)
        with self.assertRaises(ValueError):
            to_timestr([])

    def test_custom_format(self):
        """测试自定义格式"""
        self.assertEqual(to_timestr("2021-01-01", "%Y/%m/%d"), "2021/01/01")
        self.assertEqual(to_timestr("2021-01-01 12:30:45", "%H:%M"), "12:30")


if __name__ == "__main__":
    unittest.main()
