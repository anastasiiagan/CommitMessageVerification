import sys, inspect
import os

import subprocess
from collections import namedtuple
from inspect import getmembers, isfunction, signature

class CommitMessageVerification:
    def __init__(self, proj_dict:str):
        self.project_directory = proj_dict
    
    def change_directory(self):
        if self.project_directory.startswith('.'):
            self.project_directory = os.getcwd() + '\\' + self.project_directory[2:]

        self.project_directory = self.project_directory.replace('\\', '/')
        print(f"Repository directory: {self.project_directory}")

        try:
            fd = os.open( self.project_directory, os.O_RDONLY )
            os.fchdir(fd)
            return fd
        except FileNotFoundError:
            print(f"The specified directory could not be found: {self.project_directory}")
        except PermissionError:
            print(f"You don't have permission to enter directory: {self.project_directory}")
    
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
        fd = self.change_directory()    #changes directory and returns it

        # Get repository status
        out, err = self.get_repository_status()
        print(f'Repository actual status:')
        print(f'out = {out}\nerr = {err}\n')
        # Use 'git diff --cached' instead ?

        class_dict = self.get_cls_func_sign()
        print(f'Classes with functions with signatures: {class_dict}\n')

        try:
            os.close( fd )
        except TypeError:
            print("The directory wasn't specified. Couldn't close it.")


if __name__ == '__main__':
    project_directory = str(sys.argv[1])
    verification = CommitMessageVerification(project_directory)
    verification.get_message()