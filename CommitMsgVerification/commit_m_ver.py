import contextlib
import importlib
import inspect
import itertools
import os
import sys
from collections import namedtuple
from inspect import getmembers, isfunction, signature
from pathlib import Path

import git
from enums import CommitMessage
import argparse

my_parser = argparse.ArgumentParser(description='Print the type of conventional commit')
my_parser.add_argument('-p', '--path',
                       metavar='path',
                       type=str,
                       default='.',
                       help='The path to git repository')
args = my_parser.parse_args()



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

    @staticmethod
    def get_changed_files(repository):
        """Returns files that were changed and staged."""
        diff_objects = repository.index.diff(repository.head.commit, create_patch=False)
        return [(d.a_rawpath.decode("utf-8"), d.change_type) for d in diff_objects]

    @staticmethod
    def get_modules_to_import(changed_files):
        """Returns modules."""
        cwd = Path.cwd()

        modules = []
        for file_dir, file_type in changed_files:
            file_name = os.path.basename(file_dir)[:-3]
            path_to_file = os.path.join(cwd,file_dir)

            try:
                spec = importlib.util.spec_from_file_location(file_name, path_to_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules.append(module)
            except FileNotFoundError:
                print(f"File {file_name} doesn't exist. Unable to install module.")

        return modules

    @staticmethod
    def get_functions_signature_dict(list_of_functions):
        func_sign = {}
        for func_name, func_obj in list_of_functions:
            func_signature = signature(func_obj)
            func_sign[func_name] = func_signature
        return func_sign
    
    @staticmethod
    def cls_in_module(module):
        md = module.__dict__
        return [
            md[c] for c in md if (
                isinstance(md[c], type) and md[c].__module__ == module.__name__
            )
        ]

    #@staticmethod <- nie mozna bo uruchamia inna metode w klasie
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

            class_dict[cls_obj.__name__] = func_signature_dict
        return class_dict

    @staticmethod
    def compare_fun_params(func_param_after, func_param_before):
        result = CommitMessage.FIX
        if len(func_param_after) > len(func_param_before):
            result = CommitMessage.FEAT
            new_params = list(set(func_param_after) - set(func_param_before))
            for param in new_params:
                print(f'Param default = {param.default}')
                if param.default == inspect._empty:
                    # Added argument is not optional
                    return CommitMessage.MAJOR
        return result


    def compare_directories(self, cls_after_changes, cls_before_changes):
        result = CommitMessage.FIX
        for cls_obj, func_list in cls_after_changes.items():
            if cls_obj in cls_before_changes:
                func_before_changes = cls_before_changes[cls_obj]
                for func_name, func_sign in func_list.items():
                    if func_name in func_before_changes:
                        func_param_after = func_sign.parameters.values()
                        func_param_before = func_before_changes[func_name].parameters.values()
                        comparison_commit = self.compare_fun_params(func_param_after,func_param_before)
                        result = CommitMessage.get_max_by_value(result, comparison_commit)
                    else:
                        # the method was added after the change
                        result = CommitMessage.get_max_by_value(result, CommitMessage.FEAT)
            else:
                # the class was added after the change
                print(f'class {cls_obj} is new')
                result = CommitMessage.get_max_by_value(result, CommitMessage.FEAT)

        for cls_obj, func_list in cls_before_changes.items():
            if cls_obj not in cls_after_changes:
                # the class is missing after the changes
                return CommitMessage.MAJOR._name_

        return result._name_

    
    def get_message(self):
        with change_cwd(self.project_directory):
            # Initialize git repository based on changed directory
            self.repository = git.Repo()

            # Get staged changed files status
            self.changed_files = self.get_changed_files(self.repository)
            # print(f'Changed files: {self.changed_files}\n')

            modules_imported = self.get_modules_to_import(self.changed_files)
            # print(f'Modules imported: {modules_imported}\n')

            cls_after_changes = self.get_cls_func_sign(modules_imported)

            with GitStash(self.repository, self.changed_files):
                modules_imported = self.get_modules_to_import(self.changed_files)
                cls_before_changes = self.get_cls_func_sign(modules_imported)

            print(f'Classes with signatures after changes: {cls_after_changes}\n')

            print(f'Classes with signatures before changes: {cls_before_changes}\n')

            print(f'RESULT:    {self.compare_directories(cls_after_changes, cls_before_changes)}')

            



if __name__ == '__main__':
    verification = CommitMessageVerification(args.path)
    verification.get_message()
