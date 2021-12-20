#! /usr/bin/env python3

import os
import re


# ======================================================================================================================
import sys


class Framespec(object):
    """
    A class that manages the framespec features of a group of files.

    En example, given a list of files like:

        file.1.ext
        file.2.ext
        file.3.ext
        file.4.ext
        file.5.ext
        file.6.ext
        file.7.ext
        file.8.ext
        file.9.ext
        file.10.ext

    Would be associated with a framespec string:

        1-10

    Or for a more complicated example, give a list of files like:

        file.1.ext
        file.2.ext
        file.4.ext
        file.6.ext
        file.10.ext
        file.20.ext
        file.30.ext

    Would be associated with a framespec string:

        1,2-6x2,10-30x10
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 step_delimiter="x",
                 pattern=None,
                 prefix_group_numbers=None,
                 frame_group_num=None,
                 postfix_group_numbers=None,
                 two_pass_sorting=True):
        """
        Set up some basic object level variables.

        :param step_delimiter:
                The string that is used to identify the step size. For example if the character 'x' is used, then you
                might see a framespec that looks like this: 1-10x2. If omitted, defaults to 'x'.
        :param pattern:
                By default, the frame number is assumed to be the last group of numbers in a file name. If there are
                more than one set of numbers in file name, then only the last set is used as a frame number. Anything
                before the frame number is considered the prefix. Anything after the frame number is considered the
                postfix.

                Examples - In all of the following examples the frame number is 100, the prefix is the portion before
                the frame number, and the postfix is the portion after the frame number:

                    filename.100.tif      <- prefix = "filename.", frame_no = "100", postfix = ".tif"
                    filename.100.         <- prefix = "filename.", frame_no = "100", postfix = "."
                    filename.100          <- prefix = "filename.", frame_no = "100", postfix = ""
                    filename100           <- prefix = "filename", frame_no = "100", postfix = ""
                    filename2.100.tif     <- prefix = "filename2.", frame_no = "100", postfix = ".tif"
                    filename2.1.100       <- prefix = "filename2.1.", frame_no = "100", postfix = ""
                    filename2.100         <- prefix = "filename2.", frame_no = "100", postfix = ""
                    filename2plus100.tif  <- prefix = "filename2plus", frame_no = "100", postfix = ".tif"
                    filename2plus100.     <- prefix = "filename2plus", frame_no = "100", postfix = "."
                    filename2plus100      <- prefix = "filename2plus", frame_no = "100", postfix = ""
                    100.tif               <- prefix = "", frame_no = "100", postfix = ".tif"
                    100.                  <- prefix = "", frame_no = "100", postfix = "."
                    100                   <- prefix = "", frame_no = "100", postfix = ""

                By default, the regex pattern used to extract the prefix, frame number, and postfix is:

                    (.*?)(\d+)(?!.*\d)(.*)

                However, if the file names do not conform to the assumptions above, a regex pattern may be supplied here
                that defines the correct way to extract the prefix, frame number, and postfix. If None, then the default
                regex above will be used. Defaults to None.
        :param prefix_group_numbers:
                A list of regex capture groups that, when combined, equals the prefix. If None, then the default list of
                [0] (meaning the first capture group) will be used. Defaults to None.
        :param frame_group_num:
                The regex capture group that contains the frame number. If None, defaults to 1 (meaning the second
                capture group).
        :param postfix_group_numbers:
                A list of regex capture groups that, when combined, equals the postfix. If None, then the default list
                of [2] (meaning the third capture group) will be used. Defaults to None.
        :param two_pass_sorting:
                If True, then the conversion of a list of files to a single string uses two passes to make for slightly
                more logical groupings of files. This is a relatively fast second pass (the number of steps needed is
                based on the number of groupings, not the number of frames). But if this additional computation is not
                desired, it may be turned off by setting this argument to False. Defaults to True.

        :return:
                Nothing.
        """

        self.step_delimiter = step_delimiter

        if pattern is None:
            self.pattern = r"(.*?)(\d+)(?!.*\d)(.*)"
        else:
            self.pattern = pattern

        if prefix_group_numbers is None:
            self.prefix_group_numbers = [0]
        else:
            self.prefix_group_numbers = prefix_group_numbers

        if frame_group_num is None:
            self.frame_group_num = 1
        else:
            self.frame_group_num = frame_group_num

        if postfix_group_numbers is None:
            self.postfix_group_numbers = [2]
        else:
            self.postfix_group_numbers = postfix_group_numbers

        self.two_pass_sorting = two_pass_sorting

        self._files = list()

        self._file_d = ""
        self._prefix_str = ""
        self._framespec_str = ""
        self._postfix_str = ""

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def files(self):
        """
        Return the list of files that the framespec refers to. These files do not necessarily have to exist on disk.

        :return:
                A list of file names with paths.
        """

        return self._files

    # ------------------------------------------------------------------------------------------------------------------
    @files.setter
    def files(self,
              files_p):
        """
        Property setter for the list of files that the framespec will manage. Adding this list of files automatically
        converts them to a framespec string.

        :param files_p:
                A list of files that will be condensed into a framespec string.

        :return:
                Nothing.
        """

        assert type(files_p) is list

        self._files = files_p
        self._convert_file_list_to_framespec_str(files_p)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def framespec_str(self):
        """
        Returns the file list compressed into a single string.

        :return:
                The file list as a single framespec string.
        """

        file_n = f"{self._prefix_str}{self._framespec_str}{self._postfix_str}"
        return os.path.join(self._file_d, file_n)

    # ------------------------------------------------------------------------------------------------------------------
    def _convert_grouped_list_into_string(self,
                                          grouped_list):
        """
        Given a grouped list, return a string that is in the framespec format.

        :param grouped_list:
                A list of integers, grouped into sub-lists by step size. For example:

                    [[1,2,3], [5, 7, 9], [100, 110, 120], [192]]

        :return:
                A framespec string. For example:

                    1-3,5-9x2,100-120x10,192
        """

        for i, chunk in enumerate(grouped_list):
            if len(chunk) == 1:
                grouped_list[i] = str(chunk[0])
            else:
                step_size = chunk[1] - chunk[0]
                first = chunk[0]
                last = chunk[-1]
                if step_size != 1:
                    grouped_list[i] = f"{first}-{last}{self.step_delimiter}{step_size}"
                else:
                    grouped_list[i] = f"{first}-{last}"

        return ",".join(grouped_list)

    # ----------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _group_list_by_step_size(integers,
                                 post_cleanup=True):
        """
        Given a list of integers, return the same list, but grouped into sub-lists by step size.

        For example, given:
            [1, 2, 3, 5, 7, 9, 20, 30, 40]

        Returns:
            [[1,2,3], [5,7,9], [20,30,40]]

        :param integers:
                A list of integers.
        :param post_cleanup:
                If True, then a second pass will be made through the resulting groupings to see if perhaps some of the
                values at the end of a group might not make more sense in the next group. This can fix issues where you
                have a result that looks like this: [1, 4], [6, 8, 10, 12, 14, 16]. In that example it would make more
                sense to have the 4 be a part of the following group. If False, this second pass is skipped. Defaults to
                True. Turning it off may lead to an infinitesimally small speed increase (might make sense for insanely
                long sequences).

        :return:
                A list of lists, where each sub-list is a sequence of numbers that differ from each other by the same
                step size.
        """

        if len(integers) == 1:
            return [[integers[0]]]

        if len(integers) == 2:
            return [[integers[0]], [integers[1]]]

        seq_list = list()

        curr_sub_list = list()
        start_new_sub_list = True
        for i, integer in enumerate(integers):

            if start_new_sub_list:
                curr_sub_list.append(integer)
                start_new_sub_list = False
                continue

            back_diff = integer - integers[i-1]
            try:
                forward_diff = integers[i+1] - integer
            except IndexError:
                forward_diff = None

            if forward_diff:
                if back_diff != forward_diff:
                    curr_sub_list.append(integer)
                    seq_list.append(curr_sub_list)
                    curr_sub_list = list()
                    start_new_sub_list = True
                    continue
            else:
                back_back_diff = integers[i-1] - integers[i-2]
                if back_back_diff == back_diff:
                    curr_sub_list.append(integer)
                elif len(curr_sub_list) == 1:
                    curr_sub_list.append(integer)
                else:
                    seq_list.append(curr_sub_list)
                    curr_sub_list = [integer]
                continue

            curr_sub_list.append(integer)

        if curr_sub_list:
            seq_list.append(curr_sub_list)

        print(f" pre-cleanup: {seq_list}")

        if post_cleanup and len(seq_list) > 1:

            # Look at every chunk except the last one
            for i, curr_chunk in enumerate(seq_list[:-1]):

                # Only deal with chunks that have more than one element
                if len(curr_chunk) > 1:
                    next_chunk = seq_list[i + 1]
                    next_chunk_len = len(next_chunk)

                    # Only move items if the next chunk is longer than the current chunk
                    if next_chunk_len > len(curr_chunk):
                        curr_chunk_last_value = curr_chunk[-1]
                        next_chunk_first_value = next_chunk[0]
                        curr_to_next_diff = next_chunk_first_value - curr_chunk_last_value

                        # No need to worry about IndexErrors because the next chunk is always > than 1 element long
                        next_chunk_step_size = next_chunk[1] - next_chunk[0]

                        # If the step size is the same it means this element probably should be in the next section.
                        if curr_to_next_diff == next_chunk_step_size:
                            value_to_move = curr_chunk[-1]
                            seq_list[i] = seq_list[i][:-1]
                            seq_list[i+1] = [value_to_move] + seq_list[i+1]

            # DEBUG
            print(f"post-cleanup: {seq_list}")

        return seq_list

    # ------------------------------------------------------------------------------------------------------------------
    def _convert_file_list_to_framespec_str(self,
                                            files):
        """
        Given a list of files, extracts the frame numbers.

        :param files:
                A list of file names. May include paths. May not include duplicate frame numbers. If duplicate frame
                numbers are present, an error is raised. The assumption is that the frame number is the last set of
                numbers in the file name. The regular expression being used is: (.*?)(\d+)(?!.*\d)(.*)

                Examples - In all of the following examples the frame number is 100, the prefix is the portion before
                the frame number, and the postfix is the portion after the frame number:

                    filename.100.tif      <- prefix = "filename.", frame_no = "100", postfix = ".tif"
                    filename.100.         <- prefix = "filename.", frame_no = "100", postfix = "."
                    filename.100          <- prefix = "filename.", frame_no = "100", postfix = ""
                    filename100           <- prefix = "filename", frame_no = "100", postfix = ""
                    filename2.100.tif     <- prefix = "filename2.", frame_no = "100", postfix = ".tif"
                    filename2.1.100       <- prefix = "filename2.1.", frame_no = "100", postfix = ""
                    filename2.100         <- prefix = "filename2.", frame_no = "100", postfix = ""
                    filename2plus100.tif  <- prefix = "filename2plus", frame_no = "100", postfix = ".tif"
                    filename2plus100.     <- prefix = "filename2plus", frame_no = "100", postfix = "."
                    filename2plus100      <- prefix = "filename2plus", frame_no = "100", postfix = ""
                    100.tif               <- prefix = "", frame_no = "100", postfix = ".tif"
                    100.                  <- prefix = "", frame_no = "100", postfix = "."
                    100                   <- prefix = "", frame_no = "100", postfix = ""

        :return:
                A string representing the entire list of files as a single entity.
        """

        if not files:
            return

        frame_nums = list()

        prefix_str = ""
        postfix_str = ""
        file_d = ""
        previous_prefix_str = None
        previous_postfix_str = None
        previous_file_d = None

        for file_p in files:

            file_d, file_n = os.path.split(file_p)

            if not file_d:
                raise ValueError(f"File {file_p} does not have a path.")

            if previous_file_d is not None:
                if previous_file_d != file_d:
                    raise ValueError("All files must live in the same directory.")
            previous_file_d = file_d

            result = re.match(self.pattern, file_n)
            if result is None:
                raise ValueError(f"File {file_n} does not contain a sequence number.")

            prefix = list()
            for prefix_group_number in self.prefix_group_numbers:
                prefix.append(result.groups()[prefix_group_number])
            prefix_str = "".join(prefix)

            postfix = list()
            for postfix_group_number in self.postfix_group_numbers:
                postfix.append(result.groups()[postfix_group_number])
            postfix_str = "".join(postfix)

            if previous_prefix_str is not None and previous_postfix_str is not None:
                if prefix_str != previous_prefix_str or postfix_str != previous_postfix_str:
                    raise ValueError("All file names must be the same (except for the sequence number).")
            previous_prefix_str = prefix_str
            previous_postfix_str = postfix_str

            frame_nums.append(int(result.groups()[self.frame_group_num]))

        frame_nums.sort()
        frame_nums = self._group_list_by_step_size(frame_nums, self.two_pass_sorting)

        self._file_d = file_d
        self._prefix_str = prefix_str
        self._framespec_str = self._convert_grouped_list_into_string(frame_nums)
        self._postfix_str = postfix_str


# ======================================================================================================================
# TESTING
# ======================================================================================================================

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
def main():

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
            framespec_obj.files = files_list
        except ValueError as e:
            print(e)
            return

        print(framespec_obj.framespec_str)
        print("\n\n")


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    import random
    main()
