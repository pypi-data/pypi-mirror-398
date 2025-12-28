import unittest
import logging
import io
import re
from pathlib import Path
from vxutils.logger import loggerConfig, VXColoredFormatter, stop_logger


class TestLoggerConfig(unittest.TestCase):
    def tearDown(self):
        stop_logger()

    def test_console_colored_output_contains_message(self):
        buf = io.StringIO()
        logger = loggerConfig(level="DEBUG", async_logger=False, colored=True, force=True, stream=buf)
        logging.info("hello")
        output = buf.getvalue()
        self.assertIn("hello", output)

    def test_file_without_ansi_escape(self):
        log_file = Path("test_logger_file.log")
        if log_file.exists():
            log_file.unlink()
        logger = loggerConfig(level="DEBUG", filename=log_file, async_logger=False, force=True)
        logging.warning("warn")
        logging.error("error")
        content = log_file.read_text(encoding="utf-8")
        self.assertNotRegex(content, "\x1b\[")
        stop_logger()
        log_file.unlink(missing_ok=True)

    def test_async_listener_and_stop(self):
        buf = io.StringIO()
        logger = loggerConfig(level="DEBUG", async_logger=True, colored=False, force=True, stream=buf)
        logging.info("async")
        stop_logger()
        s = buf.getvalue()
        self.assertIn("async", s)

    def test_force_resets_handlers(self):
        logger1 = loggerConfig(level="INFO", async_logger=False, force=True)
        count1 = len(logger1.handlers)
        logger2 = loggerConfig(level="INFO", async_logger=False, force=True)
        self.assertEqual(len(logger2.handlers), count1)

    def test_named_logger_no_propagate(self):
        buf = io.StringIO()
        root_buf = io.StringIO()
        for h in list(logging.root.handlers):
            logging.root.removeHandler(h)
        root_handler = logging.StreamHandler(root_buf)
        logging.root.addHandler(root_handler)
        logger = loggerConfig(level="INFO", async_logger=False, colored=False, force=True, logger="vxutils.test", stream=buf)
        lg = logging.getLogger("vxutils.test")
        lg.info("named")
        self.assertEqual(lg.propagate, False)
        self.assertIn("named", buf.getvalue())
        self.assertNotIn("named", root_buf.getvalue())


class TestVXColoredFormatter(unittest.TestCase):
    def test_format_with_reset_and_override(self):
        VXColoredFormatter.set_color(logging.INFO, "XCOLOR")
        formatter = VXColoredFormatter(reset_code="RESET")
        record = logging.makeLogRecord({"levelno": logging.INFO, "msg": "abc"})
        formatted = formatter.format(record)
        self.assertTrue(formatted.startswith("XCOLOR"))
        self.assertTrue(formatted.endswith("RESET"))


if __name__ == "__main__":
    unittest.main()
