from functools import wraps
import os
from pathlib import Path
import shutil
import sys

# Set to track copied modules
copied_modules = set()

def get_relative_path(module_path: Path, sys_path: list) -> Path:
    """Compute the relative path of module_path relative to sys.path entries."""
    module_path = module_path.resolve()
    for base in sys_path:
        base_path = Path(base).resolve()
        try:
            if module_path.is_relative_to(base_path):
                return module_path.relative_to(base_path)
        except ValueError:
            continue
    return Path(module_path.name)

class patch_find_spec:
    def __init__(self, cwd, run_path, python_path):
        self.cwd = cwd
        self.run_path = run_path
        self.python_path = python_path

    def __call__(self, spec):
        if spec is not None and spec.origin and spec.origin != "built-in" and os.path.isfile(spec.origin):
            module_name = spec.name
            if module_name not in copied_modules:
                module_path = Path(spec.origin)

                dest_path = None

                if module_path.is_relative_to(self.cwd):
                    dest_path = self.run_path / module_path.relative_to(self.cwd)
                elif self.python_path:
                    relative_path = get_relative_path(module_path, sys.path)
                    dest_path = self.python_path / relative_path

                if dest_path:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(module_path, dest_path)
                    copied_modules.add(module_name)

    # def __call__(self, fullname, path, target=None):
    #     spec = self.original_find_spec(fullname, path, target)

    #     if spec is not None and spec.origin and spec.origin != "built-in" and os.path.isfile(spec.origin):
    #         module_name = spec.name
    #         if module_name not in copied_modules:
    #             module_path = Path(spec.origin)

    #             dest_path = None

    #             if module_path.is_relative_to(self.cwd):
    #                 dest_path = self.run_path / module_path.relative_to(self.cwd)
    #             elif self.python_path:
    #                 relative_path = get_relative_path(module_path, sys.path)
    #                 dest_path = self.python_path / relative_path

    #             if dest_path:
    #                 dest_path.parent.mkdir(parents=True, exist_ok=True)
    #                 shutil.copy2(module_path, dest_path)
    #                 copied_modules.add(module_name)

    #     return spec

# def patch_find_spec(cwd, run_path, python_path, original_find_spec):
#     """Create a patched version of find_spec that copies .py files."""
#     @wraps(original_find_spec)
#     def patched_find_spec(fullname, path, target=None):
#         spec = original_find_spec(fullname, path, target)

#         if spec is not None and spec.origin and spec.origin != "built-in" and os.path.isfile(spec.origin):
#             module_name = spec.name
#             if module_name not in copied_modules:
#                 module_path = Path(spec.origin)

#                 dest_path = None

#                 if module_path.is_relative_to(cwd):
#                     dest_path = run_path / module_path.relative_to(cwd)
#                 elif python_path:
#                     relative_path = get_relative_path(module_path, sys.path)
#                     dest_path = python_path / relative_path

#                 if dest_path:
#                     dest_path.parent.mkdir(parents=True, exist_ok=True)
#                     shutil.copy2(module_path, dest_path)
#                     copied_modules.add(module_name)

#                 # elif python_path:
#                 #     relative_path = get_relative_path(module_path, sys.path)
#                 #     dest_path = python_path / relative_path
#                 #     dest_path.parent.mkdir(parents=True, exist_ok=True)

#                 #     shutil.copy2(module_path, dest_path)
#                 #     copied_modules.add(module_name)

#                     # if module_path.suffix == '.py':
#                 # elif module_path.suffix == '.py':
#                 #     relative_path = get_relative_path(module_path, sys.path)
#                 #     dest_path = path / relative_path
#                 #     dest_path.parent.mkdir(parents=True, exist_ok=True)
#                 #     try:
#                 #         shutil.copy2(module_path, dest_path)
#                 #         print(f"Copied {module_path} to {dest_path} (relative: {relative_path})")
#                 #         copied_modules.add(module_name)
#                 #     except Exception as e:
#                 #         print(f"Failed to copy {module_path}: {e}")
#                 # else:
#                 #     print(f"Skipped copying {module_path} (not a .py file)")

#         return spec
#     return patched_find_spec
