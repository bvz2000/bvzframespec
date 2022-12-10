#! /usr/bin/env python3

import sys

from bvzframespec import Framespec


# ----------------------------------------------------------------------------------------------------------------------
def process_cmd_line():
    """
    A super janky command line interpreter.

    :return:
        A tuple containing the start, end, and max values for the random list generator.
    """

    # Super janky command line interface
    if "-h" in sys.argv:
        print(f"{sys.argv[0]} [-rand] [-start NN] [-end NN] [-max NN]")
        print()
        print("If you don't use any options, the test suite is pre-defined and will run on a fixed")
        print("set of test sequences.")
        print()
        print("Use the optional -rand option to run the tool on a random sequence. To change the")
        print("parameters of this random sequence, use -start to choose the starting value,")
        print("-end to chose the ending value, and -max to choose the maximum number of values.")
        sys.exit(0)

    max_num_files = 5
    start = 1
    end = 7

    if "-start" in sys.argv:
        i = sys.argv.index("-start") + 1
        try:
            start = int(sys.argv[i])
        except ValueError:
            print("start value must be an integer")

    if "-end" in sys.argv:
        i = sys.argv.index("-end") + 1
        try:
            end = int(sys.argv[i])
        except ValueError:
            print("end value must be an integer")

    if "-max" in sys.argv:
        i = sys.argv.index("-max") + 1
        try:
            max_num_files = int(sys.argv[i])
        except ValueError:
            print("max value must be an integer")

    if end - start < max_num_files - 1:
        print("Error: end - start is less than the maximum number of values.")
        sys.exit()

    return start, end, max_num_files


# ----------------------------------------------------------------------------------------------------------------------
def build_random_list(start,
                      end,
                      max_values):
    """
    Build a random list of numbers between the start and end, consisting of max_values entries.

    :param start:
        The lowest number allowed.
    :param end:
        The highest number allowed.
    :param max_values:
        The number of values in the list.

    :return:
        A list consisting of "max_values" number of random values, in ascending order.
    """

    output = list()

    for i in range(max_values):
        rand = None
        counter = 0
        while rand is None or (rand in output and counter < 1000):
            counter += 1
            rand = random.randint(start, end)
        output.append(rand)

    output.sort()

    return output


# ----------------------------------------------------------------------------------------------------------------------
def test_num_list_to_string():
    """
    Tests converting a list of numbers to a string.
    """

    # Below are some pre-defined lists. Add to this list if you want more pre-defined tests.
    test_lists = list()
    test_lists.append([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    test_lists.append([1])
    test_lists.append(([1, 8]))
    test_lists.append(([1, 8]))
    test_lists.append([1, 4, 6, 8, 10, 12, 14, 15, 18, 20])
    test_lists.append([2, 5, 8, 9, 12, 14, 15, 18, 19, 20])
    test_lists.append([3, 5, 6, 8, 9, 11, 15, 17, 18, 20])
    test_lists.append([4, 6, 7, 8, 9, 11, 12, 16, 17, 19])
    test_lists.append([4, 6, 8, 9, 10, 11, 12, 13, 15, 20])
    test_lists.append([1, 2, 4, 6, 8, 9, 10, 11, 12, 14])

    # If a random test is desired, replace the above list with a random list
    if "-rand" in sys.argv:
        start, end, max_values = process_cmd_line()
        test_lists = [build_random_list(start=start, end=end, max_values=max_values)]
        print(f"Generating a random set of {max_values} values between {start} and {end}.")

    # Run each test
    for test_list in test_lists:

        print(test_list)

        files_list = list()
        for rand in test_list:
            files_list.append(f"/some/path/file.{rand}.tif")

        framespec_obj = Framespec()

        try:
            framespec_obj.files_list = files_list
        except ValueError as e:
            print(e)
            return

        print(framespec_obj.condensed_files_str)
        print("\n\n")


# ----------------------------------------------------------------------------------------------------------------------
def test_string_to_num_list():
    """
    Given a string, convert it to a list of files.
    """

    tests = ["/some/files.1-10,20-30x2.exr",
             "/some/files.1.exr",
             "/some/files1-100.exr",
             "/some/files1-100exr",
             "/some/files1-100x5exr",
             "/some/files.23-34.1-100.exr",
             "/some/files.1-100x5.exr",
             "/some/files.1,2,3,4.exr",
             "/some/files.1-3,5-10.exr",
             "/some/files/1-5x2,5-100x9,134,139,200-201,203-220x3.exr",
             "/some/files.exr",
             "/some/files.1-a.exr",
             "/some/files.10-1.exr"]

    framespec_obj = Framespec()

    for test in tests:
        print("\n\n\n")
        print(test)
        print("_"*40)
        framespec_obj.condensed_files_str = test
        files = framespec_obj.files_list
        for file_n in files:
            print(file_n)


# ----------------------------------------------------------------------------------------------------------------------
def edge_cases():
    """
    Do some edge case testing.
    """
    #
    # files_list = ["/some/file.1.ext",
    #               "/some/file.2.ext",
    #               "/some/file.3.ext",
    #               "/some/files.4.ext"]
    #
    # framespec_obj = Framespec()
    # framespec_obj.files_list = files_list
    # try:
    #     print(framespec_obj.files_str)
    # except ValueError as e:
    #     print(e)

    # Convert a condensed file string to a list of files.
    framespec_obj = Framespec()
    framespec_obj.condensed_files_str = "/some/files/1-5x2,5-100x9,134,139,200-201,203-220x3.exr"
    try:
        print("\n".join(framespec_obj.files_list))
    except ValueError as e:
        print(e)


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import random

    # test_string_to_num_list()
    #
    # print("\n\n\n", "="*80)
    # test_num_list_to_string()
    #
    # print("\n\n\n", "="*80)
    edge_cases()
