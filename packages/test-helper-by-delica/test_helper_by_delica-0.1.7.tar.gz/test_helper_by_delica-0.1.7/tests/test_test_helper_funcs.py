from unittest import TestCase
import test_helper_by_delica.test_helper_funcs as test_lib

def test_func_always_true(test_int1=0, test_int2=0, test_bool1=True, test_bool2=False, test_str1="", test_str2=""):
    return True

def test_func_always_false(test_int1=0, test_int2=0, test_bool1=True, test_bool2=False, test_str1="", test_str2=""):
    return False

def test_func_is_int(test_input=0):
    return type(test_input) is int

def test_func_is_int_type_error_if_false(test_input=0):
    is_int = type(test_input) is int
    if not is_int:
        raise TypeError(f"{test_input} is not an integer")
    return is_int

class Test(TestCase):
    def test_test_bool_func(self):
        # test_lib.test_bool_func(self, test_func_always_true, true_inputs=[(),(1,),(1,2),(1,2,True,False),
        #                                                                   (1,2,True,False,"A","ab")],
        #                         test_desc="always true function")
        # test_lib.test_bool_func(self, test_func_always_false, false_inputs=[(),(1,),(1,2),(1,2,True,False),
        #                                                                   (1,2,True,False,"A","ab")],
        #                         test_desc="always false function")
        # test_lib.test_bool_func(self, test_func_is_int, true_inputs=[(),(1,),(-1,),(10000,),(-10000,)],
        #                         false_inputs=[(1.0,),(-1.0,),(10000.0,),(-10000.0,),("",),("int",),(True,),(False,)],
        #                         test_desc="is int function")
        test_lib.test_bool_func(self, test_func_is_int_type_error_if_false, true_inputs=[(), (1,), (-1,), (10000,), (-10000,)],
                                false_inputs=[(1.0,), (-1.0,), (10000.0,), (-10000.0,), ("",), ("int",), (True,),
                                              (False,)],
                                test_desc="is int function with TypeError if false", error_if_false=True, error_type=TypeError)
        test = 0
