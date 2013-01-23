# CPopen

A C reimplementation of the tricky bits of Python's Popen.

It is currently implemented in a very specific way and might break under
general use.

# TODO

* Support string invocation - Currently only support array invocation
* Support after fork func
* Support all stream modes - Currently everything has to be PIPE

# Usage

import cpopen
proc = cpopen.CPopen(["echo", "3"])
proc.communictate()
