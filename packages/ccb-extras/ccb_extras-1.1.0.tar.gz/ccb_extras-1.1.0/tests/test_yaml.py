"""Unit tests"""

import pytest
from ccb_essentials.constant import UTF8
from ccb_essentials.filesystem import temporary_path

from ccb_extras.yaml import YamlFile


# Nil YAML, formatted by machine
_EMPTY_YAML = """%YAML 1.2
--- {}
"""

# YAML, with sloppy formatting
_SAMPLE_TEXT = """
    a: b
    c: 123
"""

# YAML, formatted by a machine
_SAMPLE_YAML = """%YAML 1.2
---
a: b
c: 123
"""

# YAML, formatted by man and machine
_FORMATTED_YAML = """%YAML 1.2
---
# here is some sample data from https://yaml.org/spec/1.2/spec.html
hr:  65    # Home runs
avg: 0.278 # Batting average
rbi: 147   # Runs Batted In
"""

# YAML, formatted by man and machine
_FORMATTED_YAML_EDITED = """%YAML 1.2
---
# here is some sample data from https://yaml.org/spec/1.2/spec.html
hr: 66     # Home runs
avg: 0.278 # Batting average
rbi: 147   # Runs Batted In
wins: 1000
losses: 999
"""

# YAML, with nested keys
_HIERARCHICAL_YAML = """%YAML 1.2
---
key1.key2.key3: dotted-value
key1:
  key2:
    key3: hierarchical-value
nested1: {nested2: {nested3: nested-value}}
"""


class TestYamlFile:
    """Unit tests for YamlFile()"""

    @staticmethod
    def test_empty() -> None:
        """It should initialize an empty yaml file."""
        with temporary_path() as path:
            YamlFile(path)
            with open(path, encoding=UTF8) as f:
                assert f.read() == _EMPTY_YAML

    @staticmethod
    def test_invalid_default() -> None:
        """It should fail on invalid default values."""
        with temporary_path() as path, pytest.raises(AssertionError):
            YamlFile(path, '0')

    @staticmethod
    def test_invalid_file() -> None:
        """It should fail on invalid file."""
        with temporary_path() as path:
            path.write_text('0')
            with pytest.raises(AssertionError):
                YamlFile(path)

    @staticmethod
    def test_new_file_defaults() -> None:
        """It should create a new yaml file with default values on initialization."""
        with temporary_path() as path:
            assert not path.is_file()
            YamlFile(path, _SAMPLE_TEXT)
            assert path.is_file()
            with open(path, encoding=UTF8) as f:
                assert f.read() == _SAMPLE_YAML

    @staticmethod
    def test_new_file_str_path_defaults() -> None:
        """It should create a new yaml file from a path string."""
        with temporary_path() as path:
            assert not path.is_file()
            YamlFile(str(path), _SAMPLE_TEXT)
            assert path.is_file()
            with open(path, encoding=UTF8) as f:
                assert f.read() == _SAMPLE_YAML

    @staticmethod
    def test_empty_file_defaults() -> None:
        """It should write default values to an empty file on initialization."""
        with temporary_path() as path:
            path.touch()
            YamlFile(path, _SAMPLE_TEXT)
            with open(path, encoding=UTF8) as f:
                assert f.read() == _SAMPLE_YAML

    @staticmethod
    def test_yaml_doc() -> None:
        """It should share its yaml doc for convenience."""
        with temporary_path() as path:
            doc = YamlFile(path, _SAMPLE_TEXT).yaml_doc
            assert isinstance(doc, dict)
            assert doc['a'] == 'b'
            assert doc['c'] == 123

    @staticmethod
    def test_path() -> None:
        """It should know its own path."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            assert yaml.path == path

    @staticmethod
    def test_document_to_string() -> None:
        """It should serialize to string."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            assert yaml.to_string == _SAMPLE_YAML

    @staticmethod
    def test_get_value() -> None:
        """It should get a value."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            assert yaml.get_value("a") == "b"
            assert yaml.get_value("c") == 123

    @staticmethod
    def test_missing_value() -> None:
        """It should not get a missing value."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            assert yaml.get_value("z") is None

    @staticmethod
    def test_default_value() -> None:
        """It should accept a default for a missing value."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            assert yaml.get_value("z", 123) == 123

    @staticmethod
    def test_load_file() -> None:
        """It should load yaml from a file."""
        with temporary_path() as path:
            with open(path, 'w', encoding=UTF8) as f:
                f.write(_SAMPLE_YAML)
            yaml = YamlFile(path)
            assert yaml.get_value("a") == "b"
            assert yaml.get_value("c") == 123

    @staticmethod
    def test_set_value() -> None:
        """It should set a value and write to disk."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            yaml.set_value("answer", 42)
            found_answer = False
            with open(path, encoding=UTF8) as f:
                for line in f.readlines():
                    if line.rstrip() == "answer: 42":
                        found_answer = True
        assert found_answer

    @staticmethod
    def test_formatting() -> None:
        """It should update values and preserve formatting on a round-trip from disk."""
        with temporary_path() as path:
            with open(path, 'w', encoding=UTF8) as f:
                f.write(_FORMATTED_YAML)
            yaml = YamlFile(path)
            yaml.set_value("wins", 1000)
            yaml.set_value("losses", 999)
            yaml.set_value("hr", yaml.get_value("hr") + 1)
            with open(path, encoding=UTF8) as f:
                assert f.read() == _FORMATTED_YAML_EDITED

    @staticmethod
    def test_get_delimited_value_no_delimiter() -> None:
        """It should handle a key as a plain string when no delimiter is provided."""
        with temporary_path() as path:
            yaml = YamlFile(path, _HIERARCHICAL_YAML)
            for key in [
                'key1.key2.key3',
                'nested1.nested2.nested3',
            ]:
                assert yaml.get_delimited_value(key, key_delimiter='') == yaml.get_value(key)

    @staticmethod
    def test_get_delimited_value() -> None:
        """It should handle a key as a compound key when a delimiter is provided."""
        with temporary_path() as path:
            yaml = YamlFile(path, _HIERARCHICAL_YAML)
            for key, delimiter, expected in [
                ('key1.key2.key3', '.', 'hierarchical-value'),
                ('key1/key2/key3', '/', 'hierarchical-value'),
                ('nested1.nested2.nested3', '.', 'nested-value'),
                ('nested1/nested2/nested3', '/', 'nested-value'),
            ]:
                assert yaml.get_delimited_value(key, key_delimiter=delimiter) == expected

    @staticmethod
    def test_set_delimited_value_no_delimiter() -> None:
        """It should handle a key as a plain string when no delimiter is provided, and write to disk."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            yaml.set_delimited_value("the.answer.is", 42, key_delimiter='')
            found_answer = False
            with open(path, encoding=UTF8) as f:
                for line in f.readlines():
                    if line.rstrip() == "the.answer.is: 42":
                        found_answer = True
        assert found_answer

    @staticmethod
    def test_set_delimited_value() -> None:
        """It should handle a key as a compound when na delimiter is provided, and write to disk."""
        with temporary_path() as path:
            yaml = YamlFile(path, _SAMPLE_TEXT)
            yaml.set_delimited_value("the.answer.is", 42, key_delimiter='.')
            found_answer = False
            with open(path, encoding=UTF8) as f:
                for line in f.readlines():
                    if line.rstrip() == "the: {answer: {is: 42}}":
                        found_answer = True
        assert found_answer
