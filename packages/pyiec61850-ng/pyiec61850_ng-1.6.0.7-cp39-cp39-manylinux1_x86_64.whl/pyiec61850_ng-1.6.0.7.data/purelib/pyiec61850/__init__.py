import os, sys, ctypes
_package_dir = os.path.dirname(os.path.abspath(__file__))
for lib_file in os.listdir(_package_dir):
    if lib_file.startswith('libiec61850.so'):
        try:
            lib_path = os.path.join(_package_dir, lib_file)
            ctypes.CDLL(lib_path)
            break
        except Exception as e:
            print(f'Warning: Failed to load {lib_file}: {e}')
