from unittest import TestCase

def run_single_test(unittest_obj, assert_func, test_func, test_input=(), expected_output=(),
                    test_desc=""):
    """Runs a single test using an unittest TestCase object.

    Parameters
    ----------
    unittest_obj : TestCase
        The unittest TestCase object that should be used to run the test.
    assert_func : function
        The unittest assertion function that should be used to verify the result of the test.
    test_func : function
        The function that should be tested.
    test_input : tuple, default=()
        The input tuple that will be passed to the test function.
    expected_output : tuple, default=()
        The expected output that should be returned by the test function.
    test_desc : str, default=""
        A description of the test that should be printed to stdout.

    Returns
    -------
    None

    Raises
    ______
    AssertionError
        Raised if the test fails.
    """
    assert isinstance(unittest_obj, TestCase)
    assert callable(assert_func)
    # test = getattr(TestCase, assert_func.__name__)
    # assert callable(getattr(unittest_obj, assert_func.__name__))
    assert callable(test_func)
    print("Testing " + test_desc)
    input_string = str(test_input)
    expected_output_string = str(expected_output)
    use_assert_raises = False
    error_type = None
    use_assert_raises = False
    if type(expected_output) is type:
        use_assert_raises = issubclass(expected_output, Exception)
        if use_assert_raises:
            error_type = expected_output

    if use_assert_raises:
        assert error_type is not None
        # error_type = Exception
        # if len(expected_output) > 0:
        #     error_type = expected_output[0]
        assert error_type is Exception or issubclass(error_type, Exception)
        with unittest_obj.assertRaises(error_type) as context_manager:
            test_func(*test_input)
        raised_exception = context_manager.exception
        if raised_exception is not None:
            print(f"ERROR MESSAGE: {str(raised_exception)}")

    else:
        test_output = test_func(*test_input)
        if hasattr(test_output, "__len__"):
            assert len(test_output) == len(expected_output)
        if type(test_output) is tuple:
            assert_func(*test_output, *expected_output)
        else:
            assert_func(test_output, expected_output)

        # assert_func(test_output, *expected_output)
    print(f"SUCCESS: input={input_string} -> output={expected_output_string}")


def run_func_tests(unittest_obj, assert_func, test_func, input_output_pairs, test_desc=""):
    """Runs a set of unittest tests for a specified function.

    Parameters
    ----------
    unittest_obj : TestCase
        The unittest TestCase object that should be used to run the tests.
    assert_func : function
        The unittest assertion function that should be used to verify the results of the tests.
    test_func : function
        The function that should be tested.
    input_output_pairs : list
        List of the input/output tuples that should be passed to the test function. The length of this list determines
        the number of tests that will be run.
    test_desc : str, default="",
        A description of the tests that should be printed to stdout.

    Returns
    -------
    None

    Raises
    ______
    AssertionError
        Raised if any of the tests fail (stdout messages allow the user to easily determine which test case failed).

    """
    assert isinstance(unittest_obj, TestCase)
    assert callable(test_func)
    assert callable(assert_func)
    assert type(input_output_pairs) == list
    assert type(test_desc) == str
    print("TESTING " + test_desc.upper())
    io_pairs = []
    for io_pair in input_output_pairs:
        if io_pair != ():
            io_pairs.append(io_pair)
    num_tests = len(io_pairs)
    test_num = 1
    for io_pair in io_pairs:
        assert type(io_pair) == tuple
        assert len(io_pair) == 1 or len(io_pair) == 2
        test_input = io_pair[0]
        expected_output = ()
        if len(io_pair) == 2:
            expected_output = io_pair[1]
        print(f"Test #{test_num} of {num_tests}")
        run_single_test(unittest_obj, assert_func, test_func, test_input, expected_output,
                        f"{test_func.__name__} function for input " + str(test_input))
        test_num += 1
    print(f"ALL {num_tests} TESTS COMPLETED FOR {test_desc.upper()}\n")


def test_bool_func(unittest_obj, test_func, true_inputs=None, false_inputs=None, error_if_false=False, error_type=Exception,
                   test_desc="", success_desc=""):
    """Runs a set of unittest tests for a function that returns a boolean value.

    Parameters
    ----------
    unittest_obj : TestCase
        The unittest TestCase object that should be used to run the tests.
    test_func : function
        The boolean function that should be tested.
    true_inputs : list
        List of input tuples that should cause the test function to return True.
    false_inputs : list
        List of input tuples that should cause the test function to return False.
    error_if_false : bool, default=False
        Boolean flag for whether the function should raise an error when the condition it evaluates is False.
    error_type : type, default=Exception
        The type of exception that should be raised for False results.
    test_desc : str, default="",
        A description of the tests that should be printed to stdout.

    Returns
    -------
    None

    Raises
    ______
    AssertionError
        Raised if any of the tests fail (stdout messages allow the user to easily determine which test case failed).

    """
    assert isinstance(unittest_obj, TestCase)
    assert callable(test_func)
    if true_inputs is None:
        true_inputs = []
    else:
        assert type(true_inputs) == list
    if false_inputs is None:
        false_inputs = []
    else:
        assert type(false_inputs) == list
    assert type(false_inputs) == list
    assert type(error_if_false) == bool
    assert issubclass(error_type, Exception)
    assert type(test_desc) == str
    assert type(success_desc) == str
    # print("TESTING " + test_desc.upper())
    assert_func = unittest_obj.assertEqual
    test_inputs = true_inputs.copy()
    test_inputs.extend(false_inputs)
    expected_outputs = [(True)] * len(true_inputs)
    false_output = False
    if error_if_false:
        false_output = error_type
    expected_outputs.extend([(false_output)] * len(false_inputs))
    num_tests = len(test_inputs)
    assert num_tests == len(expected_outputs)
    if num_tests > 0:
        io_pairs = [()]*num_tests
        io_index = 0
        while io_index < num_tests:
            test_input = test_inputs[io_index]
            expected_output = expected_outputs[io_index]
            io_pairs[io_index] = (test_input, expected_output)
            io_index += 1
        run_func_tests(unittest_obj, assert_func, test_func, io_pairs, test_desc)


    # test_num = 1
    # num_tests = len(true_inputs) + len(false_inputs)
    # for true_input in true_inputs:
    #     assert type(true_input) == tuple
    #     print(f"Test #{test_num} of {num_tests}")
    #     run_single_test(unittest_obj, assert_func, test_func, true_input, (True), f"{test_func.__name__} function for input "
    #                     + str(true_input), success_desc)
    #     test_num += 1
    # for false_input in false_inputs:
    #     assert type(false_input) == tuple
    #     print(f"Test #{test_num} of {num_tests}")
    #     if error_if_false:
    #         assert_func = unittest_obj.assertRaises
    #     run_single_test(unittest_obj, assert_func, test_func, false_input, TypeError,
    #                     f"{test_func.__name__} function for input "
    #                     + str(false_input), success_desc)
    # test_num += 1
