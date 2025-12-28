# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import os
import os.path
from typing import Iterator, Tuple


def yield_module_names_and_python_file_paths(
        source_directory,  # type: str
):
    # type: (...) -> Iterator[Tuple[str, str]]
    """
    Recursively traverses a source directory and yields tuples of Python module names as used in import statements and their corresponding file paths.

    Args:
        source_directory: Source directory to traverse.

    Yields:
        (module_name, python_file_path) tuples.
    """
    for root, directories, files in os.walk(source_directory):
        # Skip hidden directories
        directories[:] = [d for d in directories if not d.startswith('.')]

        # Skip hidden files
        files[:] = [f for f in files if not f.startswith('.')]

        relpath = os.path.relpath(root, source_directory)

        python_file_names = []
        python_file_paths = []

        for file in files:
            file_name, file_ext = os.path.splitext(file)
            if file_ext == '.py':
                python_file_names.append(file_name)
                python_file_paths.append(os.path.join(root, file))

        # Directly handle all Python files in `os.path.curdir` (e.g., '.')
        if relpath == os.path.curdir:
            for python_file_name, python_file_path in zip(python_file_names, python_file_paths):
                yield python_file_name, python_file_path
        # In other directories,
        # if there is a Python file named `__init__` within the directory
        # handle the directory itself (pointing to the Python file named `__init__`)
        # and python files within it (excluding the Python file named `__init__`)
        # if there is not
        # we directly handle all Python files
        else:
            relpath_components = relpath.split(os.path.sep)

            if '__init__' in python_file_names:
                index_of_init = python_file_names.index('__init__')
                module_name = '.'.join(relpath_components)
                yield module_name, python_file_paths[index_of_init]

                for python_file_name, python_file_path in zip(python_file_names, python_file_paths):
                    if python_file_name != '__init__':
                        module_name_components = []
                        module_name_components.extend(relpath_components)
                        module_name_components.append(python_file_name)
                        module_name = '.'.join(module_name_components)
                        yield module_name, python_file_path
            else:
                for python_file_name, python_file_path in zip(python_file_names, python_file_paths):
                    module_name_components = []
                    module_name_components.extend(relpath_components)
                    module_name_components.append(python_file_name)
                    module_name = '.'.join(module_name_components)
                    yield module_name, python_file_path
