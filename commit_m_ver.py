import sys, inspect
import os
from pathlib import Path
import contextlib

import git

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
    repository = None
    changed_files = []

    def __init__(self, proj_dict:str):
        self.project_directory = proj_dict
    
    # def get_repository_status(self):
    #     process = subprocess.Popen(['git', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     return namedtuple('Std', 'out, err')(process.stdout.read(), process.stderr.read())

    # Returns files that were changed and staged
    def get_changed_files(self):
        diff_objects = self.repository.index.diff(self.repository.head.commit, create_patch=False)
        return [(d.a_rawpath, d.change_type) for d in diff_objects]

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
            # Initialize git repository based on changed directory
            self.repository = git.Repo('.')


            # Get staged changed files status
            self.changed_files = self.get_changed_files()
            print(f'Changed files: {self.changed_files}\n')

            # class_dict = self.get_cls_func_sign()
            # print(f'Classes with functions with signatures: {class_dict}\n')


if __name__ == '__main__':
    project_directory = str(sys.argv[1])
    if project_directory:
        verification = CommitMessageVerification(project_directory)
        verification.get_message()
    else:
        print('The directory of repository might be provided')