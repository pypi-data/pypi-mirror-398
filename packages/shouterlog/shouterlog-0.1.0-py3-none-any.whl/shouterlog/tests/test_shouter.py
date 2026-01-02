import logging
from io import StringIO
import pytest
from python_modules.shouterlog import Shouter 

def test_initialize_logger():
    # Test initializing the logger
    shouter = Shouter()
    assert shouter.logger is not None
    assert shouter.logger.level == logging.INFO

def test_shout_default():
    # Test the default shout behavior
    shouter = Shouter()
    log_capture_string = StringIO()
    shouter.logger.addHandler(logging.StreamHandler(log_capture_string))
    shouter.logger.setLevel(logging.DEBUG)

    shouter.debug()

    log_capture_string.seek(0)
    log_output = log_capture_string.getvalue()
    assert "=" * 50 in log_output

@pytest.mark.parametrize("output_type,expected,mess", [
    ("dline", "=" * 50, None),
    ("line", "-" * 50, None),
    ("pline", "." * 50, None),
    ("HEAD1", "\n" + "=" * 50 + "\n" + "-" * ((50 - len("TEST")) // 2 - 1) + "TEST" + "-" * ((50 - len("TEST")) // 2 - 1) + " \n" + "=" * 50, "TEST"),
    # Add more cases for other output_types
])
def test_shout_various_types(output_type, expected, mess):
    # Test shout with various output types
    shouter = Shouter()
    log_capture_string = StringIO()
    shouter.logger.addHandler(logging.StreamHandler(log_capture_string))
    shouter.logger.setLevel(logging.DEBUG)

    shouter.debug(output_type=output_type, mess=mess)

    log_capture_string.seek(0)
    log_output = log_capture_string.getvalue()
    assert expected in log_output

def test_shout_custom_length():
    # Test shout with a custom line length
    custom_length = 30
    shouter = Shouter()
    log_capture_string = StringIO()
    shouter.logger.addHandler(logging.StreamHandler(log_capture_string))
    shouter.logger.setLevel(logging.DEBUG)

    shouter.debug(dotline_length=custom_length)

    log_capture_string.seek(0)
    log_output = log_capture_string.getvalue()
    assert "=" * custom_length in log_output


