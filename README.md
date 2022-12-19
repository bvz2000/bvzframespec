# **bvzframespec**

---

A library responsible for converting numbered lists of files to a "condensed string" and back again.

---

# Basic Examples:

Given a list of files like:

```
/my/file.1.ext
/my/file.2.ext
/my/file.3.ext
```
return:

```/my/file.1-3.ext```

It also works in reverse. Given:

```/my/file.1-3.ext```

return:

```
/my/file.1.ext
/my/file.2.ext 
/my/file.3.ext
```

Discontinuous ranges are also supported, Give a list of files like:

```
/my/file.1.ext
/my/file.3.ext
/my/file.5.ext
/my/file.20.ext
/my/file.21.ext
/my/file.22.ext
```
return:
```
/my/file.1-5x3,20-22.ext
```

This feature also works in reverse. Given:

```
/my/file.12-18x2,100-150x10,312.ext
```

return

```
/my/file.12.ext
/my/file.14.ext
/my/file.16.ext
/my/file.18.ext
/my/file.100.ext
/my/file.110.ext
/my/file.120.ext
/my/file.130.ext
/my/file.140.ext
/my/file.150.ext
/my/file.312.ext
```
---

# Terminology

To start with, some very basic terms need to be defined.

- **files list**: *This is simply a list of strings that differ from each other only by an integer number (example: **file.1.ext**, **file.2.ext**, **file.3.ext**). Typically, these are files on disk, but there is no requirement that they actually be existing files. Any list of strings that only differ from each other by an integer is considered a "files list".*


- **framespec**: *This is a string that represents a list of numbers in a condensed sequence of ranges with optional step sizes (example: the list of integers 1, 2, 3, 4, 5, 10, 12, 14 would be represented as the framespec string: "1-5,10-12x2").*


- **condensed file string**: *This is a representation of a **files list** where the integers have been converted to a framespec (example: **file.1-3.ext**). Again, this is typically used to represent a list of files in a condensed, human-readable format. But there is no requirement that this condensed file string actually represents files. It is merely a condensed way of representing a list of strings that differ from each other only by a unique integer. Condensed file strings **contain** framespecs. They are not framespecs in and of themselves.*



---

# Basic Usage Overview:
Using this class is relatively straightforward.

To use, start by instantiating a new framespec object. When instantiating, there are a number of attributes that may optionally be set. But for this overview we will simply stick with the defaults.

```python
from bvzframespec import Framespec

fs = Framespec()
```

Now let's assume you have a **files list** that you want to represent as a condensed string. To do that, you merely pass this list to the framespec object and then access the condensed files string parameter.

```python
fs.files_list = ["/some/file.1.ext",
                 "/some/file.2.ext",
                 "/some/file.5.ext",
                 "/some/file.7.ext",
                 "/some/file.9.ext"]

print(fs.condensed_files_str)
```

This would print: 

```/some/file.1-2,5-9x2.ext```

To do this in reverse, assume you had a condensed file string such as "/my/files.100-150x10.ext". You would simply pass this string to the framespec object and then access the files list parameter.:

```python
fs.condensed_files_str = "/my/files.100-150x10.ext"

print(fs.framespec_str)
```

This would print:
```
/my/files.100.ext
/my/files.110.ext
/my/files.120.ext
/my/files.130.ext
/my/files.140.ext
/my/files.150.ext
```

There are more nuances to the use of this class, but this covers the basic operation. The actual code contains a series of example test cases that you can peruse to gain a further understanding of how to use the Framespec object.

---

# Documentation

## Framespec Initialization:

---

When instantiating an object from the Framespec class, there are several parameters that can be set to control how this object behaves.

### **step_delimiter**

This is an optional string that is used to identify the step delimiter (the character used to denote the step size). For example if the character 'x' is used, then you might see a framespec that looks like this: "1-10x2". If the character ':' is used, then this same framespec would look like this: "1-10:2". If this argument is None or omitted, the step delimiter defaults to 'x'.

This step delimiter will also apply when supplying a condensed file string to the object.

### **frame_number_pattern**
This allows the regex pattern that is used to extract frame numbers from the file name to be overridden. If this argument is None or omitted, the regex pattern used to extract the frame number from the file name defaults to:

```(.*?)(-?\d+)(?!.*\d)(.*)```

If the default regex pattern is used, the frame number is assumed to be the last group of numbers in a file name. If there are more than one set of numbers in the file name, then only the last set is used as a frame number. Anything before the frame number is considered the ***prefix***. Anything after the frame number is considered the ***postfix***.

In all of the following examples the frame number is 100, the prefix is the portion before the frame number, and the postfix is the portion after the frame number:

- filename.100.tif      <- prefix = "filename.", frame # = "100", postfix = ".tif"
- filename.100.         <- prefix = "filename.", frame # = "100", postfix = "."
- filename.100          <- prefix = "filename.", frame # = "100", postfix = ""
- filename100           <- prefix = "filename", frame # = "100", postfix = ""
- filename2.100.tif     <- prefix = "filename2.", frame # = "100", postfix = ".tif"
- filename2.1.100       <- prefix = "filename2.1.", frame # = "100", postfix = ""
- filename2.100         <- prefix = "filename2.", frame # = "100", postfix = ""
- filename2plus100.tif  <- prefix = "filename2plus", frame # = "100", postfix = ".tif"
- filename2plus100.     <- prefix = "filename2plus", frame # = "100", postfix = "."
- filename2plus100      <- prefix = "filename2plus", frame # = "100", postfix = ""
- 100.tif               <- prefix = "", frame # = "100", postfix = ".tif"
- 100\.                <- prefix = "", frame # = "100", postfix = "."
- 100                   <- prefix = "", frame # = "100", postfix = ""

### **prefix_group_numbers**
A list of regex capture group numbers that, when combined, equals the prefix. Looking at the default regex pattern you can see - assuming you understand regex - that the first capture group (and only the first capture group) represents the prefix. If you supply a custom frame_number_pattern regex that has more than one capture group for the prefix, you will have to supply those capture group numbers here to reassemble the prefix from the captured strings. If None or omitted, then the prefix_group_numbers list contains only a single value of 0 (meaning the first capture group).

### **frame_group_num**
The regex capture group number that represents the capture group containing the frame number. Looking at the default regex pattern you can see - assuming you understand regex - that the second capture group (and only the second capture group) represents the frame number. If you supply a custom frame_number_pattern regex that captures the frame number in a different group, you will have to supply that capture group number here. If None or omitted, then the prefix_group_number contains a value of 1 (meaning the second capture group). Note: while the prefix_group_numbers and postfix_group_numbers may be lists, this value must be a single integer

### **postfix_group_numbers**
A list of regex capture group numbers that, when combined, equals the postfix. Looking at the default regex pattern you can see - assuming you understand regex - that the third capture group (and only the third capture group) represents the postfix. If you supply a custom frame_number_pattern regex that has more than one capture group for the postfix, you will have to supply those capture group numbers here to reassemble the prefix from the captured strings. If None or omitted, then the postfix_group_numbers list contains only a single value of 2 (meaning the third capture group).

### **two_pass_sorting**
If True, then the conversion of a list of files to a single string uses two passes to make for slightly more
logical groupings of files. For example, the first pass might group frame numbers like this: ```1-2,4-10x2``` While
this is a perfectly acceptable grouping, it is a little odd that it combines the 2 with the 1
as part of the first group. It makes more sense for the 2 to be grouped with the 4-10 range (for
a result that looks like this: ```1,2-10x2```). Enabling two_pass_sorting will run a second pass to
catch issues like this. 

This is a relatively fast second pass (the number of steps needed is based on
the number of groupings, not the number of frames). But if this additional computation is not desired, it
may be turned off by setting this argument to False. Defaults to True.

### **framespec_pattern**
This allows the regex pattern that is used to extract a framespec from a condensed file string to be overridden. If this argument is None or omitted, the regex pattern used to extract the framespec from a condensed file string defaults to:

    (?:-?\d+(?:-?-\d+)?(?:x\d+)?(?:,)?)+

Note: The character "x" above is actually replaced with the step_delimiter. For example, if the step_delimiter parameter described above were to be set to ":", then the default framespec_pattern would actually be:

    (?:-?\d+(?:-?-\d+)?(?:\:\d+)?(?:,)?)+

### **padding**
The amount of padding to use when converting the framespec string to a list of frames. If None, then the
amount of padding will be based on the longest frame number. If no padding is desired, padding should be set
to 0. Defaults to None.


---
# Installation

### Using PIP:
On your command line run ```pip install bvzframespec```

You may wish to install this into a virtual environment (venv) rather than directly in your system's python 
installation. Search online for 'python virtual environments' for more information on how to do this.

### Manual installation:
Download the zip file and unzip it to a location that makes sense for your use
case. Then make sure your PYTHONPATH variable contains a reference to this path with /src appended to the end.

For example:

If you unzipped the file to:

```/opt/lib/python/bvzframespec``` 

then make sure your PYTHONPATH includes: 

```/opt/lib./python/bvzframespec/src```

# Further Examples
To see these examples yourself (and inspect the code that generates them) execute the module directly.

### Example: 
Split a dis-similar list of files into sub-lists of similar files.

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/file.9.ext', '/different/path/file.8.ext', 'no_frame_number.ext', '/a/second/set/of/files.1.ext', '/a/second/set/of/files.2.ext', '/a/second/set/of/files.3.ext'] ```

Result:

```
['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/file.9.ext']
['/different/path/file.8.ext']
['no_frame_number.ext']
['/a/second/set/of/files.1.ext', '/a/second/set/of/files.2.ext', '/a/second/set/of/files.3.ext']
```


### Example: 

Display the above list of dissimilar files in a condensed, VFX style sequence of files.

Result:
```
/some/file.1-2,5-9x2.ext
/different/path/file.8.ext
no_frame_number.ext
/a/second/set/of/files.1-3.ext
```


### Example: 

Display the above list of dissimilar files in a condensed, VFX style sequence of files.

Result:
```
/some/file.1-2,5-9x2.ext missing: [3, 4, 6, 8]
/different/path/file.8.ext missing: []
no_frame_number.ext missing: []
/a/second/set/of/files.1-3.ext missing: []
```


### Example: 

Convert a list of files to a condensed file string.

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/file.9.ext']```

Result:

```/some/file.1-2,5-9x2.ext```



### Example: 

Convert a list of files to a condensed file string using : as a step delimiter.

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/file.9.ext']```

Result:

```/some/file.1-2,5-9:2.ext```



### Example: 

Convert a list of files to a condensed file string, but there is only one file.

Input:

```['/some/file.1.ext']```

Result:

```/some/file.1.ext```



### Example: 

Convert a single file to a condensed file string, but there is no frame number.

Input:

```['/some/file.ext']```

Result:

```/some/file.ext```



### Example: 

Convert a list of files to a condensed file string, but there are no directories.

Input:

```['file.1.ext', 'file.2.ext', 'file.5.ext', 'file.7.ext', 'file.9.ext']```

Result:

```file.1-2,5-9x2.ext```



### Example: 

Convert a list of files to a condensed file string, files are only numbers and extensions.

Input:

```['1.ext', '2.ext', '5.ext', '7.ext', '9.ext']```

Result:

```1-2,5-9x2.ext```



### Example: 

Convert a file list to a condensed file string, files have no extensions.

Input:

```['file.1', 'file.2', 'file.5', 'file.7', 'file.9']```

Result:

```file.1-2,5-9x2```



### Example: 

Convert a file list to a condensed file string, files are only numbers (no name or ext).

Input:

```['1', '2', '5', '7', '9']```

Result:

```1-2,5-9x2```



### Example: 

Convert a list of files to a condensed file string, file has multiple numbers.

Input:

```['file.100.1.ext', 'file.100.2.ext', 'file.100.5.ext', 'file.100.7.ext', 'file.100.9.ext']```

Result:

```file.100.1-2,5-9x2.ext```



### Example: 

Convert a list of files to a condensed file string, using negative frame numbers.

Input:

```['file.-2.ext', 'file.-1.ext', 'file.0.ext', 'file.1.ext', 'file.5.ext', 'file.7.ext', 'file.9.ext']```

Result:

```file.-2-1,5-9x2.ext```



### Example: 

Convert a list of files to a condensed file string using a custom regex pattern.
In this example, the custom pattern requires that a # symbol precede the frame number.

```['file.#1.ext', 'file.#2.ext', 'file.#5.ext', 'file.#7.ext', 'file.#9.ext']```

Result:

```file.#1-2,5-9x2.ext```



### Example: 

Convert a list of files to a condensed file string using ANOTHER custom regex pattern.
In this example, the custom pattern requires that a @ symbol precede the frame number.

Input:

```['file.@1.ext', 'file.@2.ext', 'file.@5.ext', 'file.@7.ext', 'file.@9.ext']```

Result:

```file.@1-2,5-9x2.ext```

Here is another list that does not conform to the pattern (it is missing the @ symbol).
This leads to an error message because the pattern does not see frame numbers, but instead sees
a series of file names that are not all the same.

Input:

```['file.1.ext', 'file.2.ext', 'file.5.ext', 'file.7.ext', 'file.9.ext']```

Result:

```All file names must be the same (except for the sequence number).```



### Example: 

Convert a list of integers to a framespec string.

Input:

```[1, 2, 5, 7, 9]```

Result:

```1-2,5-9x2```



### Example: 

Convert a framespec string to a list of numbers.

Input:

```1-2,5-9x2```

Result:

```[1, 2, 5, 7, 9]```



### Example: 

Convert a framespec string that has negative numbers to a list of numbers.


Input:

```-2--1,5-9x2```

Result:

```[-2, -1, 5, 7, 9]```



### Example: 

Convert a framespec string (that has a negative to positive range) to a list of numbers.

Input:

```-2-1,5-9x2```

Result:

```[-2, -1, 0, 1, 5, 7, 9]```



### Example: 

Convert a condensed file string to a list of files.

Input:

```/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr```

Result:

```
/some/files.001.exr
/some/files.003.exr
/some/files.005.exr
/some/files.014.exr
/some/files.023.exr
/some/files.032.exr
/some/files.041.exr
/some/files.050.exr
/some/files.059.exr
/some/files.068.exr
/some/files.077.exr
/some/files.086.exr
/some/files.095.exr
/some/files.134.exr
/some/files.139.exr
/some/files.200.exr
/some/files.201.exr
/some/files.203.exr
/some/files.206.exr
/some/files.209.exr
/some/files.212.exr
/some/files.215.exr
/some/files.218.exr
```


### Example: 

Convert a condensed file string to a list of files, but use 5 digits for padding.

Input:

```/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr```

Result:

```
/some/files.00001.exr
/some/files.00003.exr
/some/files.00005.exr
/some/files.00014.exr
/some/files.00023.exr
/some/files.00032.exr
/some/files.00041.exr
/some/files.00050.exr
/some/files.00059.exr
/some/files.00068.exr
/some/files.00077.exr
/some/files.00086.exr
/some/files.00095.exr
/some/files.00134.exr
/some/files.00139.exr
/some/files.00200.exr
/some/files.00201.exr
/some/files.00203.exr
/some/files.00206.exr
/some/files.00209.exr
/some/files.00212.exr
/some/files.00215.exr
/some/files.00218.exr
```


### Example: 

Convert a condensed file string to a list of files, but use an insufficient padding of 2.

Input:

```/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr```

Result:

```
/some/files.01.exr
/some/files.03.exr
/some/files.05.exr
/some/files.14.exr
/some/files.23.exr
/some/files.32.exr
/some/files.41.exr
/some/files.50.exr
/some/files.59.exr
/some/files.68.exr
/some/files.77.exr
/some/files.86.exr
/some/files.95.exr
/some/files.134.exr
/some/files.139.exr
/some/files.200.exr
/some/files.201.exr
/some/files.203.exr
/some/files.206.exr
/some/files.209.exr
/some/files.212.exr
/some/files.215.exr
/some/files.218.exr
```


### Example: 

Convert a condensed file string to a list of files, but use no padding.

Input:

```/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr```

Result:

```
/some/files.1.exr
/some/files.3.exr
/some/files.5.exr
/some/files.14.exr
/some/files.23.exr
/some/files.32.exr
/some/files.41.exr
/some/files.50.exr
/some/files.59.exr
/some/files.68.exr
/some/files.77.exr
/some/files.86.exr
/some/files.95.exr
/some/files.134.exr
/some/files.139.exr
/some/files.200.exr
/some/files.201.exr
/some/files.203.exr
/some/files.206.exr
/some/files.209.exr
/some/files.212.exr
/some/files.215.exr
/some/files.218.exr
```


### Example: 

Convert a condensed file string to a list of files, but use a colon as a step delimiter.

Input:

```/some/files.1-5:2,5-100:9,134,139,200-201,203-220:3.exr```

Result:

```
/some/files.001.exr
/some/files.003.exr
/some/files.005.exr
/some/files.014.exr
/some/files.023.exr
/some/files.032.exr
/some/files.041.exr
/some/files.050.exr
/some/files.059.exr
/some/files.068.exr
/some/files.077.exr
/some/files.086.exr
/some/files.095.exr
/some/files.134.exr
/some/files.139.exr
/some/files.200.exr
/some/files.201.exr
/some/files.203.exr
/some/files.206.exr
/some/files.209.exr
/some/files.212.exr
/some/files.215.exr
/some/files.218.exr
```


### Example: 

Convert a condensed file string to a list of frame numbers.

Input:

```/some/files.1-5x2,5-100x9,134,139,200-201,203-220x3.exr```

Result:

```[1, 3, 5, 14, 23, 32, 41, 50, 59, 68, 77, 86, 95, 134, 139, 200, 201, 203, 206, 209, 212, 215, 218]```



### Example: 

String does not contain a framespec.

Input:

```/some/files.exr```

Result:

```['/some/files.exr']```



### Example: 

Framespec is a single frame.

Input:

```/some/files.1.exr```

Result:

```['/some/files.1.exr']```



### Example Error Case: 

Not all the files are in the same directory.

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/another/file.9.ext']```

Result:

```All files must live in the same directory.```



### Example Error Case: 

Not all the files have the same name (prefix).

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/thing.9.ext']```

Result:

```All file names must be the same (except for the sequence number).```



### Example Error Case: 

Not all the files have the same name (postfix).

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/file.9.tif']```

Result:

```All file names must be the same (except for the sequence number).```



### Example Error Case: 

Not all the files have frame numbers.

Input:

```['/some/file.1.ext', '/some/file.2.ext', '/some/file.5.ext', '/some/file.7.ext', '/some/file.ext']```

Result:

```All file names must be the same (except for the sequence number).```