import contextlib
import importlib
import inspect
import itertools
import os
import sys
from collections import namedtuple
from inspect import getmembers, isfunction, signature
from pathlib import Path
from types import new_class

import git
from enums import CommitMessage
import argparse

ObjData = namedtuple('ObjData','name obj sign')

my_parser = argparse.ArgumentParser(description='Print the type of conventional commit')
my_parser.add_argument('-p', '--path',
                       metavar='path',
                       type=str,
                       default='.',
                       help='The path to git repository')




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
    _repository = None
    changed_files = []

    def __init__(self, *args):
        args = my_parser.parse_args(args)
        self.project_directory = args.path

    def get_repository(self):
        return self._repository
      
    def set_repository(self):
        try:
            self._repository = git.Repo(self.project_directory)
        except (git.InvalidGitRepositoryError, ValueError):
            return "The path doesn't provide to git repository"


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
    def get_obj_signature(list_of_objects):
        '''Gets object's signatures.'''
        return [(obj, signature(obj)) for obj_name, obj in list_of_objects]
    
    @staticmethod
    def cls_in_module(module):
        '''Gets classes without ones from imports.'''
        md = module.__dict__
        return [
            (md[c].__name__, md[c]) for c in md if (
                isinstance(md[c], type) and md[c].__module__ == module.__name__
            )
        ]
    
    @staticmethod
    def inspect_in_modules(modules_imported, is_func):
        funcmembers = [inspect.getmembers(module, predicate=is_func) for module in modules_imported]
        return list(itertools.chain(*funcmembers))

    def get_cls_func_sign(self, modules_imported):
        '''Gets list of tuples: class_name and list of function with signatures.'''
        clsmembers = [self.cls_in_module(module) for module in modules_imported]
        clsmembers = list(itertools.chain(*clsmembers))
        # clsmembers = self.inspect_in_modules(modules_imported, inspect.isclass)
        print(f'Repository classes: {clsmembers}\n')

        return [( cls_obj,
                    self.get_obj_signature(getmembers(cls_obj, isfunction)))
                    for cls_name, cls_obj in clsmembers]

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
        cls_after_objects = set([cls_obj_sign[0] for cls_obj_sign in cls_after_changes])
        cls_before_objects = set([cls_obj_sign[0] for cls_obj_sign in cls_before_changes])
        new_classes = cls_after_objects.difference(cls_before_objects)
        deleted_classes = cls_before_objects.difference(cls_after_objects)
        same_classes = cls_after_objects.intersection(cls_before_objects)

        if deleted_classes is not []:
            print(f'Deleted classes: {deleted_classes}')
            return CommitMessage.MAJOR._name_

        if new_classes is not []:
            print(f'New classes: {new_classes}')
            result = CommitMessage.get_max_by_value(result, CommitMessage.FEAT)
        
        classes_to_compare = [(cls_obj, func_list) for cls_obj, func_list in cls_after_changes if cls_obj in same_classes]


        for cls_obj, func_list in classes_to_compare:
            func_after_objects = set([func_obj_sign[0] for func_obj_sign in func_list])
            func_before_objects = set([func_obj_sign[0] for func_obj_sign in cls_after_changes[cls_obj]])
            new_functions = func_after_objects.difference(func_before_objects)
            deleted_functions = func_before_objects.difference(func_after_objects)
            same_functions = func_after_objects.intersection(func_before_objects)

            if deleted_classes is not []:
                print(f'Deleted functions: {deleted_functions}')
                return CommitMessage.MAJOR._name_

            if new_functions is not []:
                print(f'New functions: {new_classes}')
                result = CommitMessage.get_max_by_value(result, CommitMessage.FEAT)
            
            functions_to_compare = [(cls_obj, func_list) for cls_obj, func_list in cls_after_changes if cls_obj in same_functions]

            func_before_changes = cls_after_changes[cls_obj]
            for func_obj, func_sign in functions_to_compare:
                if result == CommitMessage.MAJOR:
                    return result._name_
                func_param_after = func_sign.parameters.values()
                func_param_before = func_before_changes[func_obj].parameters.values()
                comparison_commit = self.compare_fun_params(func_param_after,func_param_before)
                result = CommitMessage.get_max_by_value(result, comparison_commit)

        return result._name_

    
    def get_message(self):
        with change_cwd(self.project_directory):
            # Initialize git repository based on changed directory
            # self.set_repository()
            # self._repository = self.get_repository() # if None -> break?
            self._repository = git.Repo()

            self.changed_files = self.get_changed_files(self._repository)
            modules_imported = self.get_modules_to_import(self.changed_files)
            cls_after_changes = self.get_cls_func_sign(modules_imported)

            with GitStash(self._repository, self.changed_files):
                modules_imported = self.get_modules_to_import(self.changed_files)
                cls_before_changes = self.get_cls_func_sign(modules_imported)

            print(f'RESULT:    {self.compare_directories(cls_after_changes, cls_before_changes)}')

            
if __name__ == '__main__':
    verification = CommitMessageVerification('-p', '..')
    verification.get_message()
