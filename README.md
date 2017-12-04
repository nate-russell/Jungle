# Jungle (STILL UNDER ACTIVE DEV)
The Python Playground. A place to practice the ins and outs of python, software engineering, algorithms and interview questions.

# TODO
1. Figure out how to handle the occlusion of test case init cost from the decorator based profiler
2. How to specify test dimensions through decorator **kwargs
3. How best to handle special metrics (not total time and peak net ram)
4. How to limit decorator to fixed time allowances


# How it works
There are 2 halves of this repo. In the util directory, there are classes for profiling, testing and reporting. These enable the automation of evaluation and reporting for classes found in the content dir. The content directory has classes and tests for implementations of data structures, algorithms, design patterns, etc. This is

## Content
### Data Structures and Algorithms
Lets say we want to compare different algorithms/implementations for sorting. To ensure continuity and automation in testing, each implementation should inherit from the same sorting prototype class. This prototype defines the api needed by its child classes which might be the builtin mergesort, a custom written quicksort, and any ole bubblesort. The prototype class has test methods that take anywhere from 1 to 3 numeric arguments where these arguments serve as potential dimensions along which the algorithms should be evalauted. A test case for sorting is simply to sort an iterable of n objects using only comparisons. The test case can have two dimensions: 'N' the number of objects in the list and perhaps 'R' a measure of how ordered the list are already.


## Utilities
### Automated Testing
We need to test on 3 fronts.
1. Do the Content implementations do what they are supposed to? (Did mergesort actually sort?)
2. Are Content prototype and implementation classes coherent in their API (Did my custom quicksort overide the sorting prototype clss API correctly?)
3. Does the profiling and reporting work properly  (Do all of my Utility scripts work without throwing errors or get something wrong)


### JungleProfiler
An easy to use decorator that can be added to any test case of a prototype class found in the Content dir. It wraps around test cases that




### Reporting
The JungleProfiler when used as a decorator on a test case returns itself and can dump all of the information it gathered into human friendly HTML files or strings. This includes plots of . The website allows for quick browsing of these


