#! /usr/bin/env python3

import os
import re


# ======================================================================================================================
class Framespec(object):
    """
    A class that manages the framespec features of a group of files.

    Name definitions:

    framespec -> This is a string that represents a list of integers. For example 1-10x2,20-30x2
    condensed file name -> This is a string that represents a sequence of files and includes a framespec as part of the
                           string. For example: /some/file.1-10x2,20-30x2.ext

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

    And a condensed file string of:
        file.1-10.ext

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

    And a condensed file string of:
        file.1,2-6x2,10-30x10.ext

    It works in both directions.

    A condensed file string of:

        file.1,2-6x2,10-30x10.ext

    Would be associated with a list of files like:

        file.1.ext
        file.2.ext
        file.4.ext
        file.6.ext
        file.10.ext
        file.20.ext
        file.30.ext
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 step_delimiter="x",
                 frame_number_pattern=None,
                 prefix_group_numbers=None,
                 frame_group_num=None,
                 postfix_group_numbers=None,
                 two_pass_sorting=True,
                 framespec_pattern=None,
                 padding=None):
        """
        Set up some basic object level variables.

        :param step_delimiter:
            The string that is used to identify the step size. For example if the character 'x' is used, then you might
            see a framespec that looks like this: 1-10x2. If omitted, defaults to 'x'.
        :param frame_number_pattern:
            The regex pattern that is used to extract frame numbers from the file name. If None, then a default regex
            pattern is used:

            (.*?)(-?\d+)(?!.*\d)(.*)

            Defaults to None.

            If the default regex pattern is used, the frame number is assumed to be the last group of numbers in a file
            name. If there are more than one set of numbers in the file name, then only the last set is used as a frame
            number. Anything before the frame number is considered the prefix. Anything after the frame number is
            considered the postfix.

            Examples - In all of the following examples the frame number is 100, the prefix is the portion before the
            frame number, and the postfix is the portion after the frame number:

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

        :param prefix_group_numbers:
            A list of regex capture group numbers that, when combined, equals the prefix. If None, then the default list
            of [0] (meaning the first capture group) will be used. Defaults to None.
        :param frame_group_num:
            The regex capture group number that contains the frame number. If None, defaults to 1 (meaning the second
            capture group). Defaults to None.
        :param postfix_group_numbers:
            A list of regex capture group numbers that, when combined, equals the postfix. If None, then the default
            list of [2] (meaning the third capture group) will be used. Defaults to None.
        :param two_pass_sorting:
            If True, then the conversion of a list of files to a single string uses two passes to make for slightly more
            logical groupings of files. This is a relatively fast second pass (the number of steps needed is based on
            the number of groupings, not the number of frames). But if this additional computation is not desired, it
            may be turned off by setting this argument to False. Defaults to True.
        :param framespec_pattern:
            The pattern used to extract the framespec from a condensed file string. If None, the default pattern is
            used:

            (?:-?\d+(?:-?-\d+)?(?:x\d+)?(?:,)?)+

            Note: The character "x" above is actually replaced with the step_delimiter. Defaults to None.
        :param padding:
            The amount of padding to use when converting the framespec string to a list of frames. If None, then the
            amount of padding will be based on the longest frame number. If no padding is desired, padding should be set
            to 0. Defaults to None.

        :return:
                Nothing.
        """

        assert type(step_delimiter) is str
        assert frame_number_pattern is None or type(frame_number_pattern) is str
        assert prefix_group_numbers is None or type(prefix_group_numbers) is list
        assert frame_group_num is None or type(frame_group_num) is int
        assert postfix_group_numbers is None or type(postfix_group_numbers) is list
        assert type(two_pass_sorting) is bool

        self.step_delimiter = step_delimiter

        if frame_number_pattern is None:
            self.frame_number_pattern = r"(.*?)(-?\d+)(?!.*\d)(.*)"
        else:
            self.frame_number_pattern = frame_number_pattern

        if framespec_pattern is None:
            self.framespec_pattern = r'(?:-?\d+(?:-?-\d+)?(?:' + step_delimiter + '\d+)?(?:,)?)+'
        else:
            self.framespec_pattern = framespec_pattern

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

        self.padding = padding

        self.two_pass_sorting = two_pass_sorting

        self._files_list = list()
        self._files_str = ""

        self._framespec_list = list()
        self._framespec_str = ""

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def files_list(self) -> list:
        """
        Return the list of files that the framespec refers to. These files do not necessarily have to exist on disk.

        :return:
            A list of file names with paths.
        """

        if not self._files_list:
            self._files_list = self._condensed_file_str_to_file_list(self._files_str)
        return self._files_list

    # ------------------------------------------------------------------------------------------------------------------
    @files_list.setter
    def files_list(self,
                   files_p):
        """
        Property setter for the list of files that the framespec will manage.

        :param files_p:
            A list of files that will be condensed into a framespec string.

        :return:
            Nothing.
        """

        assert type(files_p) is list

        self._files_list = files_p

        # Clear out the files_str and the framespec_str because they are no longer up to date
        self._files_str = ""
        self._framespec_str = ""

        # Extract the frame numbers as a list and store that in the frames_list
        self._framespec_list = self._split_file_list_into_prefix_and_frames_list_and_ext(files_p)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def files_str(self) -> str:
        """
        Returns the file list compressed into a single condensed filename string.

        :return:
            The file list as a single framespec string.
        """

        if not self._files_str:
            self._files_str = self._file_list_to_condensed_file_str(self._files_list)
        return self._files_str

    # ------------------------------------------------------------------------------------------------------------------
    @files_str.setter
    def files_str(self,
                  string):
        """
        Sets the condensed file name which includes a framespec.

        :param string:
            The string representation of the files including the framespec. For example: /some/files.1-100.exr

        :return:
            The file list as a single framespec string.
        """

        self._files_str = string

        # Clear out the files_list and the framespec_list because they are no longer up to date.
        self._files_list = list()
        self._framespec_list = list()

        # Extract the framespec from the string and store that
        _, self._framespec_str, _ = self._split_string_into_base_framespec_and_ext(string)

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def framespec_list(self) -> list:
        """
        Return the list of numbers that the framespec refers to. These are just the numbers, and not related to any
        files.

        :return:
            A list of integers.
        """

        if not self._framespec_list:
            if not self._framespec_str:
                return []
            self._framespec_list = self._framespec_to_frame_list(self._framespec_str)
        return self._framespec_list

    # ------------------------------------------------------------------------------------------------------------------
    @framespec_list.setter
    def framespec_list(self,
                       integers):
        """
        Property setter for the list of files that the framespec will manage.

        :param integers:
            A list of integers that will be condensed into a framespec string.

        :return:
            Nothing.
        """

        assert type(integers) is list

        for integer in integers:
            if type(integer) != int:
                raise ValueError("framespec lists must only consist of integers")

        self._framespec_list = integers

        # Clear out the files_list, the files_str, and framespec_str because they are no longer up to date.
        self._files_list = list()
        self._files_str = ""
        self._framespec_str = ""

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def framespec_str(self) -> str:
        """
        Returns the framespec list compressed into a single string.

        :return:
            The framespec list as a single framespec string.
        """

        if not self._framespec_str:
            self._framespec_str = self._frames_list_to_framespec(self._framespec_list)
        return self._framespec_str

    # ------------------------------------------------------------------------------------------------------------------
    @framespec_str.setter
    def framespec_str(self,
                      string):
        """
        Sets the framespec_str.

        :param string:
            The string representation of the files including the framespec. For example: /some/files.1-100.exr

        :return:
            The file list as a single framespec string.
        """

        self._framespec_str = string

        # Clear out the files_str, files_list, and framespec_list because they are no longer up to date.
        self._files_str = ""
        self._files_list = list()
        self._framespec_list = list()

    # ------------------------------------------------------------------------------------------------------------------
    def _convert_grouped_list_into_string(self,
                                          grouped_list) -> str:
        """
        Given a grouped list, return a string that is in the framespec format.

        :param grouped_list:
            A list of integers, grouped into sub-lists by step size. For example:

                [[1,2,3], [5, 7, 9], [100, 110, 120], [192]]

        :return:
            A framespec string. For example:

                1-3,5-9x2,100-120x10,192
        """

        assert type(grouped_list) is list
        for item in grouped_list:
            assert type(item) is list
            for sub_item in item:
                assert type(sub_item) is int

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
                                 post_cleanup=True) -> list:
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
            values at the end of a group might not make more sense in the next group. This can fix issues where you have
            a result that looks like this: [1, 4], [6, 8, 10, 12, 14, 16]. In that example it would make more sense to
            have the 4 be a part of the following group. If False, this second pass is skipped. Defaults to True.
            Turning it off may lead to an infinitesimally small speed increase (might make sense for insanely long
            sequences).

        :return:
            A list of lists, where each sub-list is a sequence of numbers that differ from each other by the same step
            size.
        """

        assert type(integers) is list
        for item in integers:
            assert type(item) is int
        assert type(post_cleanup) is bool

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

            back_diff = integer - integers[i - 1]
            try:
                forward_diff = integers[i + 1] - integer
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
                back_back_diff = integers[i - 1] - integers[i - 2]
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
                            seq_list[i + 1] = [value_to_move] + seq_list[i + 1]

        return seq_list

    # ------------------------------------------------------------------------------------------------------------------
    def _frames_list_to_framespec(self,
                                  frames) -> str:
        """
        Given a list of integers, return a framespec that represents those integers in a string form.

        For example, given:

            1
            3
            4
            22

        return: 1-5x2,22

        :param frames:
            A list of integers that we want to compress to a framespec string.

        :return:
            A framespec string that represents the list of integers in a compressed format.
        """

        assert type(frames) is list

        if not frames:
            return ""

        frame_nums = frames.copy()
        frame_nums.sort()

        frame_nums = self._group_list_by_step_size(frame_nums, self.two_pass_sorting)
        framespec_str = self._convert_grouped_list_into_string(frame_nums)

        return framespec_str

    # ------------------------------------------------------------------------------------------------------------------
    def _split_file_list_into_prefix_and_frames_list_and_ext(self,
                                                             files) -> tuple:
        """
        Given a list of files, return a tuple where the first element is the path, the second element is the prefix
        (everything leading up to the frame numbers), the third element is a list of frame numbers, and the final
        element is the text after the frame number.

        For example, given:

            /my/file.1.ext
            /my/file.3.ext
            /my/file.5.ext
            /my/file.22.ext

        return:

            ("/my/", "file.", [1, 3, 5, 22], ".ext")

        :param files:
            A list of file names. May include paths. The assumption is that the frame number is the last set of numbers
            in the file name. The actual regular expression being used to extract the frame number is defined in the
            __init__ function and may be overridden with a custom regex pattern when instantiating the object.

            If the file names contain a path, all files must be in the same directory. If not, an error is raised.

            The files must all have the same prefix (the portion before the frame number) and the same suffix (the
            portion after the frame number). If not, an error is raised.

            Examples - In all of the following examples the frame number is 100, the prefix is the portion before the
            frame number, and the postfix is the portion after the frame number:

                /my/filename.100.tif      <- path = "/my/", prefix = "filename.", frame_no = "100", postfix = ".tif"
                /my/filename.100.         <- path = "/my/", prefix = "filename.", frame_no = "100", postfix = "."
                /my/filename.100          <- path = "/my/", prefix = "filename.", frame_no = "100", postfix = ""
                /my/filename100           <- path = "/my/", prefix = "filename", frame_no = "100", postfix = ""
                /my/filename2.100.tif     <- path = "/my/", prefix = "filename2.", frame_no = "100", postfix = ".tif"
                /my/filename2.1.100       <- path = "/my/", prefix = "filename2.1.", frame_no = "100", postfix = ""
                /my/filename2.100         <- path = "/my/", prefix = "filename2.", frame_no = "100", postfix = ""
                /my/filename2plus100.tif  <- path = "/my/", prefix = "filename2plus", frame_no = "100", postfix = ".tif"
                /my/filename2plus100.     <- path = "/my/", prefix = "filename2plus", frame_no = "100", postfix = "."
                /my/filename2plus100      <- path = "/my/", prefix = "filename2plus", frame_no = "100", postfix = ""
                /my/100.tif               <- path = "/my/", prefix = "", frame_no = "100", postfix = ".tif"
                /my/100.                  <- path = "/my/", prefix = "", frame_no = "100", postfix = "."
                /my/100                   <- path = "/my/", prefix = "", frame_no = "100", postfix = ""

        :return:
            A tuple where the first element is everything up to the frame number, the second element is a list of
            integers that represents the frame numbers, and the third element is the file extension.
        """

        assert type(files) is list

        if not files:
            return "", "", "", ""

        frame_nums = list()

        prefix_str = ""
        postfix_str = ""
        file_d = ""
        previous_prefix_str = None
        previous_postfix_str = None
        previous_file_d = None

        for file_p in files:

            file_d, file_n = os.path.split(file_p)

            if previous_file_d is not None:
                if previous_file_d != file_d:
                    raise ValueError("All files must live in the same directory.")
            previous_file_d = file_d

            result = re.match(self.frame_number_pattern, file_n)
            if result is None and len(files) == 1:
                prefix_str = file_n
                frame_nums = list()
                postfix_str = ""
                previous_prefix_str = prefix_str
                previous_postfix_str = postfix_str
                continue

            if result is None and len(files) > 1:
                raise ValueError("All file names must be the same (except for the sequence number).")

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

        return file_d, prefix_str, frame_nums, postfix_str

    # ------------------------------------------------------------------------------------------------------------------
    def _file_list_to_condensed_file_str(self,
                                         files) -> str:
        """
        Given a list of files, returns a single string where the frame numbers have been converted to a framespec str.

        For example, given:

            /my/file.1.ext
            /my/file.3.ext
            /my/file.5.ext
            /my/file.22.ext

        return:

            /my/file.1-5x2,22.ext

        :param files:
            A list of file names. See the _split_file_list_into_prefix_frames_list_and_ext() function for more info.

        :return:
            A string representing the entire list of files as a single entity.
        """

        file_d, prefix_str, frame_nums, postfix_str = self._split_file_list_into_prefix_and_frames_list_and_ext(files)
        framespec_str = self._frames_list_to_framespec(frame_nums)

        prefix_str = os.path.join(file_d, prefix_str)

        return f"{prefix_str}{framespec_str}{postfix_str}"

    # ------------------------------------------------------------------------------------------------------------------
    def _framespec_to_frame_list(self,
                                 framespec) -> list:
        """
        Given a framespec, return a list.

            For example, given a string like:
                1-10x2,22-30,42

            Return a list of integers like:
                1,3,5,7,9,22,23,24,25,26,27,28,29,30,42

        :param framespec:
            The string that contains the frames in a condensed, framespec format.

        :return:
            A list of integers.
        """

        # If there is an illegal character in the framespec, then a programming error has occurred.
        for char in framespec:
            assert char in "0123456789-," + self.step_delimiter

        output = list()

        chunks = framespec.split(",")
        for chunk in chunks:
            if self.step_delimiter in chunk:
                range_str, step_str = chunk.split(self.step_delimiter)
            else:
                range_str = chunk
                step_str = "1"

            if "--" in range_str:
                start_str, end_str = range_str.rsplit("--", 1)
                end_str = "-" + end_str
            elif "-" in range_str:
                start_str, end_str = range_str.rsplit("-", 1)
            else:
                start_str = end_str = range_str

            start = int(start_str)
            end = int(end_str)
            step = int(step_str)

            if start > end:
                temp = start
                start = end
                end = temp

            if start != end:
                output.extend(range(start, end + 1, step))
            else:
                output.append(start)

        output = list(set(output))
        output.sort()

        return output

    # ------------------------------------------------------------------------------------------------------------------
    def _split_string_into_base_framespec_and_ext(self,
                                                  string) -> tuple:
        """
        Given a string, return a tuple that contains the base, framespec string, and extension.

        For example:
            given /my/file.1-3,7-11x2.ext
            return ("/my/file.", "1-3,7-11x2", ".ext")

        :param string:
            The string that contains the framespec/

        :return:
            The framespec string that was in the string passed.
        """

        result = re.search(self.framespec_pattern, string)
        if not result:
            return string, "", ""

        base = string[:result.span()[0]]
        ext = string[result.span()[1]:]
        framespec = string[result.span()[0]:result.span()[1]]

        return base, framespec, ext

    # --------------------------------------------------------------------------------------------------------------
    def _condensed_file_str_to_file_list(self,
                                         string) -> list:
        """
        Given a string, extract the framespec portion and converts that to a list of files. For example: given
        /some/files.1-3.exr, this will return:

        /some/files.1.exr
        /some/files.2.exr
        /some/files.3.exr

        :param string:
            The string to convert.

        :return:
            A list of expanded files. Does not test whether these files exist on disk or not.
        """

        output = list()

        result = re.search(self.framespec_pattern, string)
        if not result:
            return [string]

        base, framespec, ext = self._split_string_into_base_framespec_and_ext(string)

        frames = self._framespec_to_frame_list(framespec)

        if self.padding is None:
            self.padding = len(str(max(frames)))

        for frame in frames:
            if self.padding == 0:
                output.append(f"{base}{frame}{ext}")
            else:
                output.append(f"{base}{str(frame).rjust(self.padding, '0')}{ext}")

        return output


# ======================================================================================================================
def main():
    """
    Example usages.
    """

    # Convert a list of files to a condensed file string.
    print("\n\n\nExample: Convert a list of files to a condensed file string.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["/some/file.1.ext",
                                    "/some/file.2.ext",
                                    "/some/file.5.ext",
                                    "/some/file.7.ext",
                                    "/some/file.9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string, but use a colon as a step delimiter instead of x.
    print("\n\n\nExample: Convert a list of files to a condensed file string using : as a step delimiter.")
    framespec_obj = Framespec(step_delimiter=":")
    try:
        framespec_obj.files_list = ["/some/file.1.ext",
                                    "/some/file.2.ext",
                                    "/some/file.5.ext",
                                    "/some/file.7.ext",
                                    "/some/file.9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string, but there is only one file.
    print("\n\n\nExample: Convert a list of files to a condensed file string, but there is only one file.")
    framespec_obj = Framespec(step_delimiter=":")
    try:
        framespec_obj.files_list = ["/some/file.1.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a single file to a condensed file string, but there is no frame number.
    print("\n\n\nExample: Convert a single file to a condensed file string, but there is no frame number.")
    framespec_obj = Framespec(step_delimiter=":")
    try:
        framespec_obj.files_list = ["/some/file.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string, but there are no directories.
    print("\n\n\nExample: Convert a list of files to a condensed file string, but there are no directories.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["file.1.ext",
                                    "file.2.ext",
                                    "file.5.ext",
                                    "file.7.ext",
                                    "file.9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string, files are only numbers and extensions.
    print("\n\n\nExample: Convert a list of files to a condensed file string, files are only numbers and extensions.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["1.ext",
                                    "2.ext",
                                    "5.ext",
                                    "7.ext",
                                    "9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a file list to a condensed file string, files are only names and numbers (no extensions).
    print("\n\n\nExample: Convert a file list to a condensed file string, files have no extensions.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["file.1",
                                    "file.2",
                                    "file.5",
                                    "file.7",
                                    "file.9"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a file list to a condensed file string, files are only numbers (no name or ext).
    print("\n\n\nExample: Convert a file list to a condensed file string, files are only numbers (no name or ext).")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["1",
                                    "2",
                                    "5",
                                    "7",
                                    "9"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string, file has multiple numbers.
    print("\n\n\nExample: Convert a list of files to a condensed file string, file has multiple numbers.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["file.100.1.ext",
                                    "file.100.2.ext",
                                    "file.100.5.ext",
                                    "file.100.7.ext",
                                    "file.100.9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string, using negative frame numbers.
    print("\n\n\nExample: Convert a list of files to a condensed file string, using negative frame numbers.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_list = ["file.-2.ext",
                                    "file.-1.ext",
                                    "file.0.ext",
                                    "file.1.ext",
                                    "file.5.ext",
                                    "file.7.ext",
                                    "file.9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string using a custom regex pattern.
    print("\n\n\nExample: Convert a list of files to a condensed file string using a custom regex pattern.")
    print("In this example, the custom pattern requires that a # symbol precede the frame number.")
    # The regex pattern requires that a # symbol precede the frame number - and that # symbol is being captured in a
    # separate capture group.
    # Because the grouping has changed (there are two prefix groups in the regex pattern), the prefix_group_numbers, the
    # frame_group_num, and the postfix_group_numbers all have to be defined as well.
    framespec_obj = Framespec(frame_number_pattern=r"(.*?)(#)(-?\d+)(?!.*\d)(.*)",
                              prefix_group_numbers=[0, 1],
                              frame_group_num=2,
                              postfix_group_numbers=[3])
    try:
        framespec_obj.files_list = ["file.#1.ext",
                                    "file.#2.ext",
                                    "file.#5.ext",
                                    "file.#7.ext",
                                    "file.#9.ext"]
        print(framespec_obj.files_list)
        print(framespec_obj.files_str)
    except ValueError as e:
        print(e)

    # Convert a list of files to a condensed file string using a custom regex pattern.
    print("\n\n\nExample: Convert a list of files to a condensed file string using ANOTHER custom regex pattern.")
    print("In this example, the custom pattern requires that a @ symbol precede the frame number.")
    # The regex pattern requires that a @ symbol precede the frame number, but the @ symbol is NOT being captured in a
    # separate capture group.
    # Because the grouping has not changed the prefix_group_numbers, the frame_group_num, and the postfix_group_numbers
    # may all be left as defaults.
    framespec_obj = Framespec(frame_number_pattern=r"(.*?@)(-?\d+)(?!.*\d)(.*)")
    try:
        files_list = ["file.@1.ext",
                      "file.@2.ext",
                      "file.@5.ext",
                      "file.@7.ext",
                      "file.@9.ext"]
        print(files_list)
        framespec_obj.files_list = files_list
        print(framespec_obj.files_str)

        print("\nHere is another list that does not conform to the pattern (it is missing the @ symbol).")
        print("This leads to an error message because the pattern does not see frame numbers, but instead sees")
        print("a series of file names that are not all the same.")
        files_list = ["file.1.ext",
                      "file.2.ext",
                      "file.5.ext",
                      "file.7.ext",
                      "file.9.ext"]
        print(files_list)
        framespec_obj.files_list = files_list
        print(framespec_obj.files_str)

    except ValueError as e:
        print(e)

    # Convert a list of numbers to a framespec string
    print("\n\n\nExample: Convert a list of integers to a framespec string.")
    framespec_obj = Framespec()
    try:
        framespec_obj.framespec_list = [1, 2, 5, 7, 9]
        print(framespec_obj.framespec_list)
        print(framespec_obj.framespec_str)
    except ValueError as e:
        print(e)

    # Convert a framespec string to a list of numbers
    print("\n\n\nExample: Convert a framespec string to a list of numbers.")
    framespec_obj = Framespec()
    try:
        framespec_obj.framespec_str = "1-2,5-9x2"
        print(framespec_obj.framespec_str)
        print(framespec_obj.framespec_list)
    except ValueError as e:
        print(e)

    # Convert a framespec string that has negative numbers to a list of numbers
    print("\n\n\nExample: Convert a framespec string that has negative numbers to a list of numbers.")
    framespec_obj = Framespec()
    try:
        framespec_obj.framespec_str = "-2--1,5-9x2"
        print(framespec_obj.framespec_str)
        print(framespec_obj.framespec_list)
    except ValueError as e:
        print(e)

    # Convert a framespec string that has a negative to positive range to a list of numbers
    print("\n\n\nExample: Convert a framespec string (that has a negative to positive range) to a list of numbers.")
    framespec_obj = Framespec()
    try:
        framespec_obj.framespec_str = "-2-1,5-9x2"
        print(framespec_obj.framespec_str)
        print(framespec_obj.framespec_list)
    except ValueError as e:
        print(e)

    # Convert a condensed file string to a list of files.
    print("\n\n\nExample: Convert a condensed file string to a list of files.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_str = "/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr"
        print(framespec_obj.files_str, "\n")
        print("\n".join(framespec_obj.files_list))
    except ValueError as e:
        print(e)

    # Convert a condensed file string to a list of files, but use 5 digits for padding.
    print("\n\n\nExample: Convert a condensed file string to a list of files, but use 5 digits for padding.")
    framespec_obj = Framespec(padding=5)
    try:
        framespec_obj.files_str = "/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr"
        print(framespec_obj.files_str, "\n")
        print("\n".join(framespec_obj.files_list))
    except ValueError as e:
        print(e)

    # Convert a condensed file string to a list of files, but use an insufficient padding of 2.
    print("\n\n\nExample: Convert a condensed file string to a list of files, but use an insufficient padding of 2.")
    framespec_obj = Framespec(padding=2)
    try:
        framespec_obj.files_str = "/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr"
        print(framespec_obj.files_str, "\n")
        print("\n".join(framespec_obj.files_list))
    except ValueError as e:
        print(e)

    # Convert a condensed file string to a list of files, but use no padding.
    print("\n\n\nExample: Convert a condensed file string to a list of files, but use no padding.")
    framespec_obj = Framespec(padding=0)
    try:
        framespec_obj.files_str = "/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr"
        print(framespec_obj.files_str, "\n")
        print("\n".join(framespec_obj.files_list))
    except ValueError as e:
        print(e)

    # Convert a condensed file string to a list of files, but use a colon instead of x as a step delimiter.
    print("\n\n\nExample: Convert a condensed file string to a list of files, but use a colon (:) as a step delimiter.")
    framespec_obj = Framespec(step_delimiter=":")
    try:
        framespec_obj.files_str = "/some/files.1-5:2,5-100:9,134,139,200-201,203-220:3.exr"
        print(framespec_obj.files_str, "\n")
        print("\n".join(framespec_obj.files_list))
    except ValueError as e:
        print(e)

    # Convert a condensed file string to a list of frame numbers.
    print("\n\n\nExample: Convert a condensed file string to a list of frame numbers.")
    framespec_obj = Framespec(padding=5)
    try:
        framespec_obj.files_str = "/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr"
        print(framespec_obj.files_str)
        print("-" * 80)
        print(framespec_obj.framespec_list)
    except ValueError as e:
        print(e)

    # String does not contain a framespec.
    print("\n\n\nExample: String does not contain a framespec.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_str = "/some/files.exr"
        print(framespec_obj.files_str)
        print("-" * 80)
        print(framespec_obj.files_list)
    except ValueError as e:
        print(e)

    # Framespec is a single frame.
    print("\n\n\nExample: Framespec is a single frame.")
    framespec_obj = Framespec()
    try:
        framespec_obj.files_str = "/some/files.1.exr"
        print(framespec_obj.files_str)
        print("-" * 80)
        print(framespec_obj.files_list)
    except ValueError as e:
        print(e)

    # Error case: Not all the files are in the same directory.
    print("\n\n\nExample: Error case: Not all the files are in the same directory.")
    files_list = ["/some/file.1.ext",
                  "/some/file.2.ext",
                  "/some/file.5.ext",
                  "/some/file.7.ext",
                  "/another/file.9.ext"]
    framespec_obj = Framespec()
    print(files_list)
    try:
        framespec_obj.files_list = files_list
    except ValueError as e:
        print(e)

    # Error case: Not all the files have the same name (prefix).
    print("\n\n\nExample: Error case: Not all the files have the same name (prefix).")
    files_list = ["/some/file.1.ext",
                  "/some/file.2.ext",
                  "/some/file.5.ext",
                  "/some/file.7.ext",
                  "/some/thing.9.ext"]
    framespec_obj = Framespec()
    print(files_list)
    try:
        framespec_obj.files_list = files_list
    except ValueError as e:
        print(e)

    # Error case: Not all the files have the same name (postfix).
    print("\n\n\nExample: Error case: Not all the files have the same name (postfix).")
    files_list = ["/some/file.1.ext",
                  "/some/file.2.ext",
                  "/some/file.5.ext",
                  "/some/file.7.ext",
                  "/some/file.9.tif"]
    framespec_obj = Framespec()
    print(files_list)
    try:
        framespec_obj.files_list = files_list
    except ValueError as e:
        print(e)

    # Error case: Not all the files have frame numbers.
    print("\n\n\nExample: Error case: Not all the files have frame numbers.")
    files_list = ["/some/file.1.ext",
                  "/some/file.2.ext",
                  "/some/file.5.ext",
                  "/some/file.7.ext",
                  "/some/file.ext"]
    framespec_obj = Framespec()
    print(files_list)
    try:
        framespec_obj.files_list = files_list
    except ValueError as e:
        print(e)


if __name__ == "__main__":
    main()
