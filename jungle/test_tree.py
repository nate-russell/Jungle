'''
Script Purpose:
Traverse content directory looking for classes that inherit from prototype classes and have test methods wrapped by JungleController.
If no modification has been made to a content file since last successful run of test_tree.py it will not be re run. (No Wasted Effort)

Definitions:
Prototype Classes = classes with 'proto' in their name
Test Methods = Bound methods belonging to a class that inherits from a prototype class
'''
import glob
import importlib
from jungle.utils.jungleprofiler import JungleController
import json
import os


class TestTreeAutomation:
    ''' Automation Code for discovering test functions used in conjunction with JungleController '''

    def __init__(self):
        directory = 'code'
        self.json_mod_log = 'content_mod_log.json'
        self.file_dict_path = 'test_tree.json'


        self.file_mod_dict = {}

        # Load File Mod Log
        self.load()

        # Iterate over all of the files in content
        for filename in glob.iglob('%s/**/*.py' % directory, recursive=True):
            if self.isfile_modified(filename):
                print('File %s has been modified since last TestTreeAutomation Call' % filename)
                self.test_file(filename)
            else:
                print('File %s has NOT been modified since last TestTreeAutomation Call' % filename)

        # Write the Test Tree and File Mod Log to JSONs
        self.write()

    def load(self):
        ''' Load Mod Log and prior TestTree '''
        # Mod Log
        try:
            with open(self.json_mod_log, mode='r') as f:
                self.old_file_mod_dict = json.load(f)
        except FileNotFoundError:
            self.old_file_mod_dict = {}
        # Last TestTree
        try:
            with open(self.file_dict_path, mode='r') as f:
                self.file_dict = json.load(f)
        except FileNotFoundError:
            self.file_dict = {}

    def isfile_modified(self, filename):
        ''' Check if file needs to be updated, also update the last modified '''
        latest_mod_time = os.stat(filename).st_mtime
        # update last mod time
        self.file_mod_dict[filename] = latest_mod_time
        try:
            if latest_mod_time <= self.old_file_mod_dict[filename]:
                return False
        except KeyError:
            print('New File Found: %s' % filename)
        return True

    def test_file(self, filename):
        ''' Discover and complete tests '''

        module_text = filename.replace('\\', '.').strip('.py')
        print('\nFile: %s\tSanitized: %s' % (filename, module_text))
        temp_module = importlib.import_module(module_text)

        prototypes = {}

        for obj_name in dir(temp_module):
            obj = getattr(temp_module, obj_name)

            try:
                obj_base = obj.__bases__
                obj_base_name = ' - '.join(ob.__name__ for ob in obj_base)
                local_test_methods = [method for method in dir(obj) if 'test' in method.lower()]
                print('\n\tObject Name: %s' % obj_name)
                print('\tObject: %s' % obj)
                print('\tObject Base: %s' % obj_base_name)

                if 'proto' in obj_base_name.lower():
                    for test_name in local_test_methods:
                        print('\t\tTest Name: %s' % test_name)
                        test_method = getattr(obj(), test_name)
                        print('\t\tTest Method: %s' % test_method)
                        try:
                            test_return = test_method()
                            if isinstance(test_return, JungleController):
                                if obj_base_name in prototypes:
                                    if test_name in prototypes[obj_base_name]:
                                        prototypes[obj_base_name][test_name].update({obj_name: 'yo yo yo'})
                                    else:
                                        prototypes[obj_base_name][test_name] = {obj_name: 'yo yo yo'}
                                else:
                                    prototypes[obj_base_name] = {test_name: {obj_name: 'yo yo yo'}}
                        except Exception as e:
                            raise e
            except AttributeError:
                pass

        if prototypes:
            self.file_dict[module_text] = prototypes
        return prototypes

    def write(self):
        ''' Write data to file '''

        print('Writing Filename Mod Log')
        with open(self.json_mod_log, mode='w') as out_file:
            json.dump(self.file_mod_dict, out_file, sort_keys=True, indent=3)

        print('Writing Test Tree')
        with open(self.file_dict_path, mode='w') as out_file:
            jdump = json.dump(self.file_dict, out_file, sort_keys=True, indent=3)


if __name__ == '__main__':
    TestTreeAutomation()
