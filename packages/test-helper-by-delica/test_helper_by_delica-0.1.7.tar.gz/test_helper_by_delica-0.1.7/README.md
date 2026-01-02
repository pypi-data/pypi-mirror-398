# test-helper-by-delica
## Purpose
This Python package simplifies the creation and execution of unittest test cases,   
in order to help programmers efficiently develop and run tests for their Python software.
## Installation
This package is available through the Python Package Index (PyPI).     
One can easily download the package with the following pip install statement:   
`pip install test_helper_by_delica`
## Getting Started
After installation, all we need to start using the package is a function that we want to test.   
For a simple example, we can define a boolean function that always returns True.  
````
def always_true():    
    return True   
````
We then use the test helper package to create a unittest TestCase object.
````
import test_helper_by_delica as test_lib 
test_obj = test_lib.create_test_obj()
````
Now we can call the boolean testing function to check whether always_true returns the expected result.
````
test_lib.test_bool_func(test_obj, always_True, true_inputs=())
````
## Current Features
## Citation
