# `resolve-module-import`

Resolves a (possibly relative) module import to its fully qualified module name.

## Features

- Resolves both absolute and relative Python module imports
- Helps with tooling (e.g., linters, code analysis) that needs to resolve imports

## Installation

```bash
pip install resolve-module-import
```

## Usage

```
resolve_module_import(
    current_module_name,  # type: str
    current_module_is_package,  # type: bool
    imported_module_name,  # type: Optional[str]
    imported_module_level,  # type: int
)
```

```python
from resolve_module_import import resolve_module_import

# from . import foo inside 'mypkg/subpkg/mymodule.py'
resolve_module_import('mypkg.subpkg.mymodule', False, 'foo', 1)
# Output: 'mypkg.subpkg.foo'

# from .. import foo inside 'pkg/bar/' (a package)
resolve_module_import('pkg.bar', True, 'foo', 2)
# Output: pkg.foo

# import sys
resolve_module_import('any.module', False, 'sys', 0)
# Output: 'sys'
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
