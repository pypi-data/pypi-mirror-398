# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from typing import Optional


def resolve_module_import(
        current_module_name,  # type: str
        current_module_is_package,  # type: bool
        imported_module_name,  # type: Optional[str]
        imported_module_level,  # type: int
):
    # type: (...) -> str
    """
    Resolves a (possibly relative) module import to its fully qualified module name.

    :param current_module_name: Fully qualified name of the current module (e.g., 'pkg.sub.mod')
    :param current_module_is_package: True if the current module is a package, False otherwise
    :param imported_module_name: The name of the module being imported, or None for things like 'from ... import foo'
    :param imported_module_level: The number of leading dots in the import (0 means absolute import)
    :return: The resolved fully qualified module name as a string
    """
    if imported_module_level > 0:
        components = current_module_name.split('.')

        if current_module_is_package:
            # In a package (__init__.py), first dot stays at current package
            number_of_components_to_drop = imported_module_level - 1
        else:
            number_of_components_to_drop = imported_module_level

        if len(components) < number_of_components_to_drop:
            raise ValueError('imported_module_level too large')
        for _ in range(number_of_components_to_drop):
            components.pop()

        if imported_module_name:
            components.append(imported_module_name)

        return '.'.join(components)
    elif imported_module_level == 0:
        if not imported_module_name:
            raise ValueError('imported_module_name cannot be None/empty for absolute imports')
        return imported_module_name
    else:
        raise ValueError('imported_module_level must == 0 for absolute imports and > 0 for relative imports')
