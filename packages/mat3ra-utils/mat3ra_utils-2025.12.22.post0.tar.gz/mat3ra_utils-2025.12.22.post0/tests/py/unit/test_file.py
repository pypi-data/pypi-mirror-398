import shutil
from pathlib import Path

from mat3ra.utils import file as utils

REFERENCE_FILE_PATH = Path(__file__).parent / "./fixtures/file_with_content.txt"
REFERENCE_FILE_CONTENT = """Content Line 1\nContent Line 2\nContent Line 3\n"""


def test_file_get_content():
    content = utils.get_file_content(REFERENCE_FILE_PATH)
    assert content == REFERENCE_FILE_CONTENT


def test_file_append_line():
    line = "Content Line 4"
    reference_file_copy_path = REFERENCE_FILE_PATH.with_name("file_with_content_test_file_append_line.txt")
    shutil.copy(REFERENCE_FILE_PATH, reference_file_copy_path)
    utils.append_line_to_file(line, reference_file_copy_path)
    content = utils.get_file_content(reference_file_copy_path)
    assert line in content
    Path.unlink(reference_file_copy_path)


def test_file_remove_line():
    pattern = "Content Line 2"
    reference_file_copy_path = REFERENCE_FILE_PATH.with_name("file_with_content_test_file_remove_line.txt")
    shutil.copy(REFERENCE_FILE_PATH, reference_file_copy_path)
    utils.remove_line_containing_pattern(pattern, reference_file_copy_path)
    content = utils.get_file_content(reference_file_copy_path)
    assert pattern not in content
    Path.unlink(reference_file_copy_path)


def test_file_get_tmp_logfile_basename():
    log_basename = utils.get_tmp_logfile_basename()
    assert log_basename.startswith("tmp-")
    assert log_basename.endswith(".log")
