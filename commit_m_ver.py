import sys, inspect
import os
from pathlib import Path
import contextlib

import git

from collections import namedtuple
from inspect import getmembers, isfunction, signature
import importlib
import itertools

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

class GitStash(object):
    """Changes git's status to the last commit and returns to provided changes on exit."""
    def __init__(self, repo, staged_files):
        self.repo=repo
        self.staged_files = staged_files

    def __enter__(self):
        self.repo.git.stash('save')
        return self.repo

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.repo.git.stash('pop')
        for changed_file in self.staged_files:
            self.repo.git.add(changed_file[0])

class CommitMessageVerification:
    repository = None
    changed_files = []

    def __init__(self, proj_dict:str):
        self.project_directory = proj_dict

    def get_changed_files(self):
        """Returns files that were changed and staged."""
        diff_objects = self.repository.index.diff(self.repository.head.commit, create_patch=False)
        return [(d.a_rawpath.decode("utf-8"), d.change_type) for d in diff_objects]

    def get_modules_to_import(self):
        """Returns modules."""
        cwd = Path.cwd()

        modules = []
        for file_dir, file_type in self.changed_files:
            file_name = os.path.basename(file_dir)[:-3]
            path_to_file = os.path.join(cwd,file_dir)

            try:
                spec = importlib.util.spec_from_file_location(file_name, path_to_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules.append(module)
            except FileNotFoundError:
                print(f"File {file_name} doesn't exist. Unable to install module.")
            # modules.append(importlib.import_module('.' + str(file_name), package=path_to_file))

        return modules

    def get_functions_signature_dict(self, list_of_functions):
        func_sign = {}
        for func_name, func_obj in list_of_functions:
            func_signature = signature(func_obj)
            func_sign[func_name] = func_signature
        return func_sign
    
    def cls_in_module(self, module):
        md = module.__dict__
        return [
            md[c] for c in md if (
                isinstance(md[c], type) and md[c].__module__ == module.__name__
            )
        ]

    def get_cls_func_sign(self, modules_imported):
        # Get list of classes
        # clsmembers = [inspect.getmembers(module, inspect.isclass) for module in modules_imported]
        clsmembers = [self.cls_in_module(module) for module in modules_imported]
        clsmembers = list(itertools.chain(*clsmembers))
        print(f'Repository classes: {clsmembers}\n')

        # Get functions for each class
        class_dict = {}
        for cls_obj in clsmembers:
            class_functions = getmembers(cls_obj, isfunction) # inspect.isfunction ?
            # print(f'Functions of class {cls_obj}: {class_functions}\n')

            func_signature_dict = self.get_functions_signature_dict(class_functions)
            # print(f'Functions with signatures: {func_signature_dict}\n')

            class_dict[cls_obj] = func_signature_dict
        return class_dict

    def compare_directories(self, cls_after_changes, cls_before_changes):
        result = "FIX"
        for cls_obj, func_list in cls_after_changes.items():
            if cls_obj in cls_before_changes:
                func_before_changes = cls_before_changes[cls_obj]
                for func_name, func_sign in func_list:
                    if func_name in func_before_changes:
                        func_sign_before_changes = func_before_changes[func_name]
                        
                        for aft, bef in zip(func_sign.parameters,func_sign_before_changes.parameters):
                            if len(aft) > len(bef):
                                result = "FEAT"
                                new_params = list(set(aft) - set(bef))
                                for param in new_params:
                                    if '=' not in param:
                                        # Added argument is not optional
                                        return "MAJOR"
                    else:
                        # the method was added after the change
                        result = "FEAT"
            else:
                # the class was added after the change
                result = "FEAT"

        for cls_obj, func_list in cls_before_changes.items():
            if cls_obj not in cls_after_changes:
                # the class is missing after the changes
                return "MAJOR"

        return result

    
    def get_message(self):
        with change_cwd(self.project_directory):
            # Initialize git repository based on changed directory
            self.repository = git.Repo()

            # Get staged changed files status
            self.changed_files = self.get_changed_files()
            # print(f'Changed files: {self.changed_files}\n')

            modules_imported = self.get_modules_to_import()
            # print(f'Modules imported: {modules_imported}\n')

            cls_after_changes = self.get_cls_func_sign(modules_imported)

            with GitStash(self.repository, self.changed_files):
                modules_imported = self.get_modules_to_import()
                cls_before_changes = self.get_cls_func_sign(modules_imported)

                # print(f'Changed files after git stash push: {self.get_changed_files()}\n')
            
            # print(f'Changed files after git stash pop: {self.get_changed_files()}\n')

            print(f'Classes with signatures after changes: {cls_after_changes}\n')

            print(f'Classes with signatures before changes: {cls_before_changes}\n')

            print(f'RESULT:    {self.compare_directories(cls_after_changes, cls_before_changes)}')

            



if __name__ == '__main__':
    project_directory = str(sys.argv[1])
    if project_directory:
        verification = CommitMessageVerification(project_directory)
        verification.get_message()
    else:
        print("The directory of repository wasn't provided")