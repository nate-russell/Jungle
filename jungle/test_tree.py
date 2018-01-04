'''
Script Purpose:
Traverse content directory looking for classes that inherit from prototype classes and have test methods wrapped by JungleController.
If no modification has been made to a content file since last successful run of test_tree.py it will not be re run. (No Wasted Effort)

Definitions:
Prototype Classes = classes with 'proto' in their name
Test Methods = Bound methods belonging to a class that inherits from a prototype class
'''
import glob
import copy
import importlib
from jungle.utils.jungleprofiler import JungleExperiment, JungleEncoder
import json
from json.decoder import JSONDecodeError
import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style('whitegrid')


class TestTreeAutomation:
    ''' Automation Code for discovering test functions used in conjunction with JungleController '''

    def __init__(self, dev=False):
        directory = 'code'
        self.json_mod_log = 'content_mod_log.json'
        self.file_dict_path = 'test_tree.json'
        self.file_mod_dict = {}
        self.dev = dev

        # Load File Mod Log
        self.load()

        # Iterate over all of the files in content
        for filename in glob.iglob('%s/**/*.py' % directory, recursive=True):
            if self.isfile_modified(filename) or self.dev:
                print('File %s has been modified since last TestTreeAutomation Call' % filename)
                self.test_file(filename)
            else:
                print('File %s has NOT been modified since last TestTreeAutomation Call' % filename)

        # Write the Test Tree and File Mod Log to JSONs
        self.post_process()
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
        except (FileNotFoundError, JSONDecodeError):
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
                            print(test_return.__repr__)
                            if isinstance(test_return, JungleExperiment):
                                if obj_base_name in prototypes:
                                    if test_name in prototypes[obj_base_name]:
                                        prototypes[obj_base_name][test_name].update({obj_name: test_return})
                                        # prototypes[obj_base_name][test_name][obj_name] = test_return
                                    else:
                                        prototypes[obj_base_name][test_name] = {obj_name: test_return}
                                else:
                                    prototypes[obj_base_name] = {test_name: {obj_name: test_return}}

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
            jdump = json.dump(self.file_dict, out_file, sort_keys=True, indent=3, cls=JungleEncoder)

    def post_process(self):
        ''' Scoop all of the related jungle controllers and combine them for reporting'''
        for file, prototype_dicts in self.file_dict.items():
            for prototype, test_dicts in prototype_dicts.items():
                for test, methods_dict in test_dicts.items():
                    print('Just called post process')
                    print(test)
                    print(methods_dict)
                    print('Calling combine jungle controllers')
                    self.combine_junglecontrollers(methods_dict)

    def combine_junglecontrollers(self, methods_dict):
        ''' dict of method keys and JungleController dictionaries'''
        df_list = []
        print('---------------------------------------\nMethods Dict')
        print(methods_dict)
        for method, jc in methods_dict.items():

            if not isinstance(jc, JungleExperiment):
                raise TypeError('arg: %s is not of type JungleController' % type(jc))
            else:
                cdf = jc.controller_df
                cdf['Method'] = method
                df_list.append(cdf)

        concat_df = pd.concat(df_list)
        sns.set_style('darkgrid')
        n_colors = len(np.unique(concat_df['Method']))
        # pal = sns.cubehelix_palette(n_colors, start=.5, rot=-.75)
        pal = sns.diverging_palette(255, 133, l=60, center="dark", n=n_colors)
        # pal = sns.color_palette("Set2", n_colors)

        print(concat_df)

        g = sns.FacetGrid(data=concat_df, col="rep", hue='Method', col_wrap=5, size=1.5)
        g = g.map(plt.plot, "kwarg: n", "walltime", marker=".")
        plt.show()

        g = sns.factorplot(data=concat_df, x='kwarg: n', y='walltime', hue='Method',
                           palette=pal, shade=True,
                           size=6, aspect=2, alpha=0.5, capsize=.2)
        g.despine(offset=10, trim=True)
        plt.title('Yo yo check it out')
        plt.show()

        sns.factorplot(data=concat_df, x='index', y='walltime', hue='Method')
        plt.show()

        sns.factorplot(data=concat_df, x='start_seconds', y='controller walltime', hue='Method')
        plt.show()


if __name__ == '__main__':
    TestTreeAutomation(dev=True)
