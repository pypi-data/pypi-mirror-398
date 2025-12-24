"""YAML helpers"""

import io
import logging
from pathlib import Path
from typing import Any

from ccb_essentials.constant import UTF8
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


log = logging.getLogger(__name__)


class YamlFile:
    """A yaml document backed by a file. The file is required to contain a yaml dictionary.
    Other values (like a single scalar) might be valid yaml, but they aren't very useful."""

    def __init__(
        self,
        path: Path | str,  # path to a yaml file
        default_values: str = '',  # serialized yaml to use if the file is empty
        encoding: str = UTF8,  # encoding for file.open()
    ):
        self._path = Path(path)

        self._yaml_parser = YAML(typ='rt')
        self._yaml_parser.version = (1, 2)
        self._yaml_parser.default_flow_style = True
        self._yaml_parser.indent(mapping=2, sequence=4, offset=2)

        loaded: dict[Any, Any] | None = None
        try:
            with open(str(self._path), encoding=encoding) as f:
                loaded = self._yaml_parser.load(f)
        except FileNotFoundError:
            pass

        if loaded is None:
            log.debug("initializing yaml file at %s", str(self._path))
            loaded = self._yaml_parser.load(default_values)
            if loaded is None:
                loaded = CommentedMap()
            assert isinstance(loaded, CommentedMap), f"default_values {default_values} is not a yaml dictionary"
            self._yaml_doc = loaded
            self._write()
        else:
            assert isinstance(loaded, CommentedMap), f"file at {self._path} is not a yaml dictionary"
            self._yaml_doc = loaded

    def __str__(self) -> str:
        return f"{type(self).__name__}({self._path})"

    @property
    def yaml_doc(self) -> dict[Any, Any]:
        """The parsed yaml document."""
        return self._yaml_doc

    @property
    def path(self) -> Path:
        """Path to the yaml file."""
        return self._path

    def _write(self) -> None:
        """Write the document to disk."""
        log.debug("write yaml")
        self._yaml_parser.dump(self._yaml_doc, self._path)

    @property
    def to_string(self) -> str:
        """Dump the document to a string."""
        s = io.StringIO()
        self._yaml_parser.dump(self._yaml_doc, s)
        return s.getvalue()

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the document."""
        if key not in self._yaml_doc or self._yaml_doc[key] is None:
            return default
        return self._yaml_doc[key]

    def set_value(self, key: str, value: Any) -> None:
        """Set a value to the document."""
        if key not in self._yaml_doc or self._yaml_doc[key] != value:
            self._yaml_doc[key] = value
            self._write()

    def get_delimited_value(self, key: str, default: Any = None, key_delimiter: str = '/') -> Any:
        """Get a value from the document. If `key_delimiter` is set, split `key` into
        a hierarchy of keys then walk the document to get the value at a leaf node."""
        if key_delimiter:
            keys = key.split(key_delimiter)
        else:
            keys = [key]

        doc = self._yaml_doc
        for k in keys:
            if k not in doc or doc[k] is None:
                return default
            doc = doc[k]
        return doc

    def set_delimited_value(self, key: str, value: Any, key_delimiter: str = '/') -> None:
        """Set a value from the document. If `key_delimiter` is set, split `key` into
        a hierarchy of keys then walk the document to set the value at a leaf node."""
        if key_delimiter:
            keys = key.split(key_delimiter)
        else:
            keys = [key]

        doc = self._yaml_doc
        dirty = False
        for i, k in enumerate(keys):
            if i < len(keys) - 1:
                if k not in doc or not isinstance(doc[k], dict):
                    doc[k] = {}
            elif k not in doc or doc[k] != value:
                doc[k] = value
                dirty = True
            doc = doc[k]

        if dirty:
            self._write()
