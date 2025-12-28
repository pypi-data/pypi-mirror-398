<img width="504" alt="time_diffz-high-resolution-logo-transparent" src="https://github.com/user-attachments/assets/6d0285dd-6cdd-4ea1-804b-561b98b0bac2" />


**Time_diffz** a library for timestamps and differences between dates

**NOTE: Time_diffz ONLY work in almost any operating system(\*1) which can support python 3.10 and above**

**\*1: Time_diffz wasn't tested on any operating system expect arch linux 
but mostly it can work on windows being that the library does not have any platform specific needs**

**Time_diffz** is an EXTREMELY ACCURATE timestamper and in calculating the differences between dates, IT DOES NOT USE ANY APPROXIMATIONS CALCULATES
EVERYTHING EXACTLY AS IT IS and nearly no for/while loops at all to provide fast performance(literally you would need less than 100 microseconds in somecases to get the amount
of months between the year 2025 and the end of the universe(year one googol), and it uses fractions based numbers to keep the numbers
exact no floating point precision loss, and it has been made for scientists and systems as the most accurate system for its own job possible,
note: in case of tropical year because of uncontrolled amount of parameters to count it to an unreliable level the J2000 is used but it's unreliable for extremely
far dates, and doc-strings for non differentiational operations are not made yet, plus future options like option to add a small amount to days like part of a second
so it can help to correct the issue of gregorian shifting slowly a whole day each 3000 years or so.

THIS LIBRARY HAS TWO MODES THE TB1 MODE OR NORMAL ONE WHICH USES STANDARD LIBRARIES
AND REQUESTS ONLY, BUT EVEN THOUGH IT'S FAST BUT YOU CAN USE THE SECOND MODE THAT
IS EVEN FASTER WHICH IS THE TB2 BUT IT NEEDS ALL TB1'S REQUIREMENTS PLUS SETUPTOOLS
AND CYTHON AND INSTALLING GMP ON YOUR COMPUTER AND BUILDING THE CYTHON SETUP FILE
WITH THIS COMMAND:
```batch
python setupfractionals.py build_ext --inplace
```
or the same but with python as python3:
```batch
python3 setupfractionals.py build_ext --inplace
```
the first mode functions starts with prefix: p*, while second mode ones
start with prefix: c*, then after the first prefix the second prefix is the
function type if it was for timestamping it would be (p/c t*) or time diff.
mode which would be (p/c d), REAL DOCUMENTATION WITH COME SOON!!
## Install

to install use the following command(note installing the library in this way
would install library requirements both main and optional):

<code>pip install Timediffz</code>

## Contribute

if you have discovered a bug, or you want to change something just open a new issue
at [Issues](https://github.com/WeDu-official/Time_diffz/issues)

## Contact

you can contact us using this [email](mailto:fplu.the.founder@gmail.com)
,and you can be a part of our community by joining [our discord server](https://discord.gg/mnduzx6yUg)
