# modwrap/module.py

"""
Safe and deterministic dynamic Python module loader.

This module provides the ModuleWrapper class, which loads Python source files
in a controlled manner, validates syntax and signatures, and exposes reflection
helpers without executing untrusted code prematurely.
"""

from __future__ import annotations

import ast
import inspect
import sys
import tokenize
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional, Union, get_type_hints
from collections.abc import Callable
from importlib.util import spec_from_file_location, module_from_spec


class ModuleWrapper:
    """
    Safe dynamic Python module loader with introspection utilities.

    The module source is read exactly once during initialization, validated,
    cached in memory, and reused for all subsequent operations.

    Attributes:
        MAX_BYTES (int): Maximum allowed file size in bytes.
    """

    MAX_BYTES: int = 1_000_000

    def __init__(
        self,
        module_path: Union[str, Path],
        allow_large_file: bool = False,
    ) -> None:
        """
        Initialize a ModuleWrapper instance.

        Args:
            module_path: Path to the Python source file.
            allow_large_file: Whether to allow files larger than MAX_BYTES.

        Raises:
            TypeError: If module_path is not a string or Path.
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the path is not a file.
            ValueError: If the file is too large or contains invalid Python.
        """
        if not isinstance(module_path, (str, Path)):
            raise TypeError("module_path must be a string or Path")

        self._path: Path = Path(module_path).expanduser().resolve(strict=True)

        if not self._path.exists():
            raise FileNotFoundError(f"File not found: {self._path}")

        if not self._path.is_file():
            raise IsADirectoryError(f"Not a file: {self._path}")

        if not allow_large_file and self._path.stat().st_size > self.MAX_BYTES:
            raise ValueError(f"File too large: {self._path}")

        self._source: str = self._read_source()
        self._validate_source()

        self._name: str = self._path.stem
        self._module: ModuleType = self._load_module()

    def __repr__(self) -> str:
        return f"ModuleWrapper(path={self._path!s}, name={self._name!r})"

    def __str__(self) -> str:
        return str(self._path)

    @property
    def module(self) -> ModuleType:
        """Loaded module object."""
        return self._module

    @property
    def path(self) -> Path:
        """Absolute file path."""
        return self._path

    @property
    def name(self) -> str:
        """Resolved module name."""
        return self._name

    @property
    def source(self) -> str:
        """Cached Python source code."""
        return self._source

    def get_callable(self, name: str) -> Callable:
        """
        Retrieve a callable by name.

        Supports both functions and Class.method notation.

        Args:
            name: Callable name.

        Returns:
            Callable object.

        Raises:
            TypeError: If the resolved object is not callable.
        """
        return self._resolve_callable(name)

    def has_callable(self, name: str) -> bool:
        """Check whether a callable exists."""
        try:
            self._resolve_callable(name)
            return True
        except Exception:
            return False

    def validate_args(self, func_name: str, expected: List[str]) -> None:
        """
        Validate that a callable defines the expected arguments.

        Args:
            func_name: Function or method name.
            expected: List of required argument names.

        Raises:
            TypeError: If an argument is missing.
        """
        fn = self._resolve_callable(func_name)
        sig = inspect.signature(fn)
        names = {p.name for p in sig.parameters.values() if p.name != "self"}

        for arg in expected:
            if arg not in names:
                raise TypeError(f"Missing expected argument: {arg}")

    def has_args(self, func_name: str, expected: List[str]) -> bool:
        """Non-raising version of validate_args()."""
        try:
            self.validate_args(func_name, expected)
            return True
        except Exception:
            return False

    def validate_signature(
        self,
        func_name: str,
        expected: Union[Dict[str, type], List[Union[str, tuple]]],
    ) -> None:
        """
        Validate a callable signature and type annotations.

        Args:
            func_name: Callable name.
            expected: Mapping or list of expected parameters.

        Raises:
            TypeError: If the signature does not match.
        """
        fn = self._resolve_callable(func_name)
        sig = inspect.signature(fn)
        params = sig.parameters
        annotations = fn.__annotations__

        if isinstance(expected, dict):
            for name, typ in expected.items():
                if name not in params:
                    raise TypeError(f"Missing parameter: {name}")
                if annotations.get(name) != typ:
                    raise TypeError(
                        f"Bad type for {name}: expected {typ}, got {annotations.get(name)}"
                    )
        elif isinstance(expected, list):
            for item in expected:
                name, typ = item if isinstance(item, tuple) else (item, None)
                if name not in params:
                    raise TypeError(f"Missing parameter: {name}")
                if typ and annotations.get(name) != typ:
                    raise TypeError(
                        f"Bad type for {name}: expected {typ}, got {annotations.get(name)}"
                    )
        else:
            raise TypeError("expected must be dict or list")

    def has_signature(
        self,
        func_name: str,
        expected: Union[Dict[str, type], List],
    ) -> bool:
        """Non-raising version of validate_signature()."""
        try:
            self.validate_signature(func_name, expected)
            return True
        except Exception:
            return False

    def get_class(
        self,
        name: Optional[str] = None,
        must_inherit: Optional[type] = None,
    ) -> Optional[type]:
        """
        Retrieve a class defined in the module.

        Args:
            name: Class name to match.
            must_inherit: Required base class.

        Returns:
            Matching class or None.
        """
        for obj in self._module.__dict__.values():
            if not isinstance(obj, type):
                continue
            if obj.__module__ != self._module.__name__:
                continue
            if name and obj.__name__ != name:
                continue
            if must_inherit and not issubclass(obj, must_inherit):
                continue
            return obj
        return None

    def get_doc(self, func_name: str) -> Optional[str]:
        """Return full docstring of a callable."""
        fn = self._resolve_callable(func_name)
        doc = inspect.getdoc(fn)
        return doc.strip() if doc else None

    def get_doc_summary(self, func_name: str) -> Optional[str]:
        """Return first line of callable docstring."""
        doc = self.get_doc(func_name)
        return doc.splitlines()[0] if doc else None

    def get_signature(self, func_path: str) -> Dict[str, Dict[str, object]]:
        """
        Extract a callable signature as structured metadata.

        Args:
            func_path: Function or Class.method path.

        Returns:
            Mapping of argument metadata.
        """
        fn = self._resolve_callable(func_path)
        sig = inspect.signature(fn)
        hints = get_type_hints(fn)

        return {
            p.name: {
                "type": str(hints.get(p.name, "Any")),
                "default": (
                    None if p.default is inspect.Parameter.empty else p.default
                ),
            }
            for p in sig.parameters.values()
            if p.name != "self"
        }

    def get_dependencies(self) -> Dict[str, List[str]]:
        """
        Analyze import dependencies of the module.

        Returns:
            Mapping of stdlib, third-party, and missing imports.
        """
        tree = ast.parse(self._source, filename=str(self._path))
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split(".", 1)[0])
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.add(node.module.split(".", 1)[0])

        stdlib, third, missing = set(), set(), set()

        for name in imports:
            try:
                __import__(name)
                mod = sys.modules.get(name)
                if mod and getattr(mod, "__file__", "").startswith(sys.base_prefix):
                    stdlib.add(name)
                else:
                    third.add(name)
            except ImportError:
                missing.add(name)

        return {
            "stdlib": sorted(stdlib),
            "third_party": sorted(third),
            "missing": sorted(missing),
        }

    def _read_source(self) -> str:
        """
        Read Python source code using PEP 263 compliant decoding.

        Returns:
            Source code as a string.

        Raises:
            ValueError: If decoding fails.
        """
        try:
            with tokenize.open(self._path) as f:
                return f.read()
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise ValueError(f"Invalid Python source encoding in {self._path}") from exc

    def _validate_source(self) -> None:
        """Validate Python syntax."""
        try:
            ast.parse(self._source, filename=str(self._path))
        except SyntaxError as exc:
            raise ValueError(f"Invalid Python syntax in {self._path}") from exc

    def _resolve_callable(self, name: str) -> Callable:
        if "." in name:
            cls_name, fn_name = name.split(".", 1)
            cls = self.get_class(cls_name)
            if not cls:
                raise AttributeError(cls_name)
            fn = getattr(cls, fn_name, None)
        else:
            fn = getattr(self._module, name, None)

        if not callable(fn):
            raise TypeError(f"{name} is not callable")

        return fn

    def _load_module(self) -> ModuleType:
        name = self._resolve_module_name()

        spec = spec_from_file_location(
            name,
            str(self._path),
            submodule_search_locations=None if "." not in name else [],
        )

        if not spec or not spec.loader:
            raise ImportError(f"Unable to load module: {name}")

        module = module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    def _resolve_module_name(self) -> str:
        root = self._find_project_root()

        if not root:
            return self._path.stem

        for base in (root / "src", root):
            try:
                rel = self._path.relative_to(base).with_suffix("")
                return ".".join(rel.parts)
            except ValueError:
                continue

        return self._path.stem

    def _find_project_root(self) -> Optional[Path]:
        p = self._path.parent
        while p != p.parent:
            if (p / "pyproject.toml").exists():
                return p
            p = p.parent
        return None
