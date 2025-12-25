import ast
import glob
import importlib
import importlib.util
import sys
from _ast import expr
from collections import namedtuple
from pathlib import Path
from typing import List, Optional

from loguru import logger

from kink import Container, di, inject


def scan():
    """Scan decorator to allow decorated classes/functions to populate the
    dependency injection container in a dynamic way, patching the module
    structure based on the scanning packages provided."""
    raise NotImplementedError()


class PackageScanner:
    """Implements the logic needed to scan components decorated with @inject,
    so they can be provided dynamically without the need to import them
    specifically in the places where they need/want to be used."""

    def __init__(self):
        self.import_targets: namedtuple = namedtuple("import_targets", ["module", "name", "alias"])
        self.inject_decorator_module: str = inject.__module__
        # Internal reference just to get the container initialised
        self.di: Container = di

    def _get_imports(self, path):
        with open(path) as fh:
            root = ast.parse(fh.read(), path)

        for node in ast.iter_child_nodes(root):
            if isinstance(node, ast.Import):
                module = []
            elif isinstance(node, ast.ImportFrom):
                module = node.module.split(".")
            else:
                continue

            for n in node.names:
                yield self.import_targets(module, n.name.split("."), n.asname)

    def _determine_module_name(self, file_path: Path) -> str:
        """Climbs all parent directories until the parents get exhausted
        without a match or we hit one of the PYTHONPATH entries in order to
        support namespaced packages (modules with folder without a
        __init__.py).

        Args:
            file_path: path of the file to produce the module name for.
        Returns:
            module_name: str
        """
        if not file_path.exists():
            raise ValueError("Invalid file path, path does not exist.")

        root_paths: list[str] = sys.path
        i: int = 0
        elements: List[str] = [file_path.name.replace(".py", "")]

        while (
            i < len(file_path.parents)
            and file_path.parents[i].is_dir()
            and str(file_path.parents[i].absolute().resolve()) not in root_paths
        ):
            elements.append(file_path.absolute().parents[i].resolve().name)
            i = i + 1
        return ".".join(reversed(elements))

    def _deal_with_python_path_for_pants(self, input_str: str, elements: List[str]) -> str:
        """Deals with module import build in the particular case that the code
        is running inside a pants test sandbox."""
        root_paths: list[str] = sys.path
        i: int = 1
        length = len(input_str.split("."))

        while i <= length and "/".join(input_str.split(".")[: length - (i)]) not in root_paths:
            i = i + 1
            elements.append(input_str.split(".")[length - i])

        return ".".join(reversed(elements))

    def perform_package_scanning(self, pattern: str, base_dir: Optional[Path] = None):
        """Performs detection of @inject decorated elements (classes) on files
        listed by the glob matcher.

        On detected classes, it performs dynamic module patching into the imported modules, so dependency injection
        is performed on the fly, adding such components into the dependency injection container for usage later on
        as requested by application elements.
        Args:
            pattern: str: Glob patter to match files against.
            base_dir: Path: base file, provided as an anchor to where apply the glob pattern (if provided).
        """
        logger.info(f"Performing package scanning for arguments pattern: {pattern}, base_dir: {base_dir}")
        elements: List[str]
        if base_dir is not None:
            if base_dir.is_dir() is False:
                raise ValueError("base_dir argument needs to be a directory.")
            elements = glob.glob(str(base_dir / pattern), recursive=True)
        else:
            elements = glob.glob(pattern, recursive=True)

        for filename in elements:
            with open(filename) as file:
                node = ast.parse(file.read())
                classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
                for class_ in classes:
                    decorators: list[expr] = class_.decorator_list
                    decorator_names: list[str] = []
                    for deco in decorators:
                        if not isinstance(deco, ast.Name):
                            if (
                                "func" in deco.__dict__.keys()
                                and deco.func
                                and "id" in deco.func.__dict__.keys()
                                and deco.func.id
                            ):
                                decorator_names.append(deco.func.id)  # type: ignore
                        else:
                            decorator_names.append(deco.id)

                    if self.inject_decorator_module.rsplit(".", maxsplit=1)[-1] in decorator_names:
                        if self.inject_decorator_module in [
                            ".".join(module.module + module.name) for module in self._get_imports(filename)
                        ]:
                            module_to_load: str = self._determine_module_name(Path(filename))

                            try:
                                mod = importlib.import_module(module_to_load)
                                logger.info(f"Imported module: {module_to_load}")
                            except TypeError:
                                # Particular case about nonsense pants sandboxes
                                sections: List[str] = module_to_load.split(".")
                                if len(sections) > 3:
                                    module_to_load = ".".join(sections[3:])
                                    nombre: List[str] = [Path(filename).name.replace(".py", "")]
                                    module_to_load = self._deal_with_python_path_for_pants(
                                        input_str=module_to_load, elements=nombre
                                    )
                                    mod = importlib.import_module(module_to_load)
                                    logger.info(f"Imported module: {module_to_load}")

                            globals().update(mod.__dict__)
                            globals()[mod.__name__] = mod
