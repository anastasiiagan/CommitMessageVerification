import sys, inspect
import os
from pathlib import Path
import contextlib

import subprocess
from collections import namedtuple
from inspect import getmembers, isfunction, signature

@contextlib.contextmanager
def change_cwd(directory):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    path = Path(directory)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)

class CommitMessageVerification:
    def __init__(self, proj_dict:str):
        self.project_directory = proj_dict
    
    def get_repository_status(self):
        process = subprocess.Popen(['git', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return namedtuple('Std', 'out, err')(process.stdout.read(), process.stderr.read())

    def get_functions_signature_dict(self, list_of_functions):
        func_sign = {}
        for func_name, func_obj in list_of_functions:
            func_signature = signature(func_obj)
            func_sign[func_name] = func_signature
        return func_sign

    def get_cls_func_sign(self):
        # Get list of classes
        clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        print(f'Repository classes: {clsmembers}\n')

        # Get functions for each class
        class_dict = {}
        for cls_name, cls_obj in clsmembers:
            class_functions = getmembers(cls_obj, isfunction) # inspect.isfunction ?
            print(f'Functions of class named {cls_name}: {class_functions}\n')

            func_signature_dict = self.get_functions_signature_dict(class_functions)
            print(f'Functions with signatures: {func_signature_dict}\n')

            class_dict[cls_name] = func_signature_dict

    
    def get_message(self):
        with change_cwd(self.project_directory):
            print(f'Current directory is {os.getcwd()}')

            # Get repository status
            out, err = self.get_repository_status()
            print(f'Repository actual status:')
            print(f'out = {out}\nerr = {err}\n')
            # Use 'git diff --cached' instead ?

            class_dict = self.get_cls_func_sign()
            print(f'Classes with functions with signatures: {class_dict}\n')


if __name__ == '__main__':
    project_directory = str(sys.argv[1])
    verification = CommitMessageVerification(project_directory)
    verification.get_message()