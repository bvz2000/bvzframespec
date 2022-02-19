#**bvzframespec**

A class responsible for converting numbered lists of files to a "condensed string" and back again.

---
---
#Examples:

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
---
#Terminology

To start with, some very basic terms need to be defined.

- **files list**: *This is simply a list of strings that differ from each other only by an integer number (example: **file.1.ext**, **file.2.ext**, **file.3.ext**). Typically, these are files on disk, but there is no requirement that they actually be existing files. Any list of strings that only differ from each other by an integer is considered a "files list".*


- **framespec**: *This is a string that represents a list of numbers in a condensed sequence of ranges with optional step sizes (example: the list of integers 1, 2, 3, 4, 5, 10, 12, 14 would be represented as the framespec string: "1-5,10-12x2").*


- **condensed file string**: *This is a representation of a **files list** where the integers have been converted to a framespec (example: **file.1-3.ext**). Again, this is typically used to represent a list of files in a condensed, human-readable format. But there is no requirement that this condensed file string actually represents files. It is merely a condensed way of representing a list of strings that differ from each other only by a unique integer. Condensed file strings **contain** framespecs. They are not framespecs in and of themselves.*



---
---
#Basic Usage Overview:
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

print(fs.files_str)
```

This would print: 

```/some/file.1-2,5-9x2.ext```

To do this in reverse, assume you had a condensed file string such as "/my/files.100-150x10.ext". You would simply pass this string to the framespec object and then access the files list parameter.:

```python
fs.files_str = "/my/files.100-150x10.ext"

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
---
#Documentation

##Framespec Initialization:

---

When instantiating an object from the Framespec class, there are several parameters that can be set to control how the this object behaves.

### **step_delimiter**

This is an optional string that is used to identify the step size. For example if the character 'x' is used, then you might see a framespec that looks like this: "1-10x2". If the character ':' is used, then this same framespec would look like this: "1-10:2". If this argument is None or omitted, the step delimiter defaults to 'x'.

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
The regex capture group number that represents the capture group containing the frame number. Looking at the default regex pattern you can see - assuming you understand regex - that the second capture group (and only the second capture group) represents the frame number. If you supply a custom frame_number_pattern regex that captures the frame number in a different group, you will have to supply that capture group number here. If None or omitted, then the prefix_group_number contains a value of 1 (meaning the second capture group).

### **postfix_group_numbers**
A list of regex capture group numbers that, when combined, equals the postfix. Looking at the default regex pattern you can see - assuming you understand regex - that the third capture group (and only the third capture group) represents the postifx. If you supply a custom frame_number_pattern regex that has more than one capture group for the postfix, you will have to supply those capture group numbers here to reassemble the prefix from the captured strings. If None or omitted, then the postfix_group_numbers list contains only a single value of 2 (meaning the third capture group).

### **two_pass_sorting**
If True, then the conversion of a list of files to a single string uses two passes to make for slightly more
logical groupings of files. This is a relatively fast second pass (the number of steps needed is based on
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
##Installation

### Using PIP:
On your command line run ```pip install bvzframespec```

You may wish to install this into a virtual environment (venv) rather than directly in your system's python 
installation. Search online for 'python virtual environments' for more information on how to do this.

### Manual installation:
```TO DO```

