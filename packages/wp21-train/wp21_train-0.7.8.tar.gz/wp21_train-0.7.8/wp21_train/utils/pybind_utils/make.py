import os
import functools
import subprocess
import importlib


def make(this_folder, module_name, package):
    """Decorator factory that ensures a pybind11 extension is compiled before use."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lib_so = f"{module_name}.so"
            lib_path = os.path.join(this_folder, lib_so)

            if not os.path.exists(lib_path):
                active_folder = os.getcwd()
                os.chdir(this_folder)

                print(f"Compiling {lib_path}...")

                cmd = [
                    "c++", "-O3", "-Wall", "-shared", "-std=c++17", "-fPIC", "-fopenmp",
                    subprocess.getoutput("python3 -m pybind11 --includes"),
                    f"{module_name}.cpp",
                    "-o", f"{module_name}"
                ]
                # Compile
                os.system(" ".join(cmd))

                # Rename to .so for stable imports
                os.system(f"mv {module_name} {lib_so}")

                os.chdir(active_folder)

            # Import dynamically
            clustering_cpp_openmp = importlib.import_module(f".{module_name}", package)

            return func(clustering_cpp_openmp, *args, **kwargs)

        return wrapper

    return decorator

