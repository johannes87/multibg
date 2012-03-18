multibg
=======

A simple command line tool for setting the background on X11 for
multiple screens separately.

Usage
-----

If you have two background images, "foo.png" and "bar.png",
the following will combine those two images into one, without distoring
the images, and then set it as a background image:

$ multibg.py foo.png bar.png

Dependencies
------------

* Python 2.7
* Esetroot, for setting the background image. This can be changed with a
  command line flag, however. See "multibg -h" for more information.
* ImageMagick / PythonMagick. I tested it with ImageMagick 6.7.6.0 and PythonMagick 0.9.7


