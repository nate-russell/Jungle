# Jungle
The Python Playground. A place to practice the ins and outs of python, software engineering, algorithms and interview questions.


## Currently Works
* **JungleController** decorator makes conducting full factorial profiling experiments on test cases easy. Also captures important information about the machine and python environment in which code operates.
* **JungleProfiler** decorator captures many forms of profiling information and prepares data for easy plotting with Seaborn. It allows for easy scoping of profiling phase so that setup and teardown sections of test cases can be excluded from benchmarking.
* **TreeTestAutomation** automates the process of **evaluation** and **reporting** by scanning through the code directory.

## In Development
* Expand profiling rigour of JungleProfiler
* Consolidation of profiling metrics across classes that inherit the same prototype test case
* README.md to include example of evaluation and reporting automation based on basic sorting methods
* Develop Web Frontend for viewing benchmarking results interactively on github pages (Big Project)
* Add basic MANOVA to full factorial tests with temporal autocorrelation.

#### Warnings
* Any test cases that involve randomization should have controllable seeds. If you don't have fixed seeds then PRNG might be responsible for variability in results in addition to runtime environments.
* Might be more, ill keep looking for shortcomings


# How it works
There are 2 halves of this repo. In the util directory, there are classes for profiling, testing and reporting. These enable the automation of **evaluation** and **reporting** for classes found in the code directory. The code directory has classes and tests for implementations of data structures, algorithms, design patterns, etc.

## Code
Lets say we want to compare different algorithms/implementations for sorting. To ensure continuity and automation in testing, each implementation should inherit from the same sorting prototype class. This prototype defines the api needed by its child classes which might be the builtin mergesort, a custom written quicksort, and any ole bubblesort. The prototype class has test methods that take anywhere from 1 to 3 numeric arguments where these arguments serve as potential dimensions along which the algorithms should be evalauted. A test case for sorting is simply to sort an iterable of n objects using only comparisons. The test case can have two dimensions: 'N' the number of objects in the list and perhaps 'R' a measure of how ordered the list are already.



