#!/usr/bin/env python

import ctypes
import ctypes.util
import sys
import argparse
import PythonMagick
import tempfile
import math
import os


def xinerama_query_screens(display = ''):
    """
    Returns the Xinerama screen infos. Returns a list of dictionaries,
    where each dictionary has the following keys:
        * screen_number
        * x_org
        * y_org
        * width
        * height
    Adapted from http://secomputing.co.uk/2008/01/22/Getting-xinerama-screen-size-info-with-Python/
    """

    path = ctypes.util.find_library('X11')
    if not path:
        raise ImportError("Could not load xlib")

    xlib = ctypes.cdll.LoadLibrary(path)

    Display = ctypes.c_void_p
    xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    xlib.XOpenDisplay.restype = ctypes.POINTER(Display)

    path = ctypes.util.find_library('Xinerama')
    if not path:
        raise ImportError("Could not load xinerama")

    xinerama = ctypes.cdll.LoadLibrary(path)

    class XineramaScreenInfo(ctypes.Structure):
        _fields_ = [
        ('screen_number', ctypes.c_int),
        ('x_org', ctypes.c_short),
        ('y_org', ctypes.c_short),
        ('width', ctypes.c_short),
        ('height', ctypes.c_short)
        ]
    xinerama.XineramaQueryScreens.restype = ctypes.POINTER(XineramaScreenInfo)
    d = xlib.XOpenDisplay(display)

    if not d:
        raise Exception("Could not open display")

    if not xinerama.XineramaIsActive(d):
        raise Exception("Xinerama not active")

    number = ctypes.c_int()
    infos = xinerama.XineramaQueryScreens(d, ctypes.byref(number))
    infos = ctypes.cast(infos, ctypes.POINTER(XineramaScreenInfo * number.value)).contents

    # we don't want to have any dependencies on the ctypes-stuff later
    infos_native = [dict([(k, getattr(info, k)) for k in dict(XineramaScreenInfo._fields_).keys()])
            for info in infos]

    xlib.XFree(infos)

    return infos_native

def stretch_and_center_image_to_screen(image, screen_info):
    image_width = image.size().width()
    image_height = image.size().height()

    screen_width = screen_info['width']
    screen_height = screen_info['height']

    scale_width = float(screen_width) / image_width
    scale_height = float(screen_height) / image_height

    scale_factor = max(scale_width, scale_height)

    dest_width = int(math.ceil(image_width * scale_factor))
    dest_height = int(math.ceil(image_height * scale_factor))
    dest_x_offset = 0
    dest_y_offset = 0

    if dest_width > screen_width:
        dest_x_offset = (dest_width - screen_width) / 2
    if dest_height > screen_height:
        dest_y_offset = (dest_height - screen_height) / 2

    image.resize(PythonMagick.Geometry(dest_width, dest_height, 0, 0))
    image.crop(PythonMagick.Geometry(screen_width, screen_height, dest_x_offset, dest_y_offset));

def get_full_bg_size(screen_infos):
    full_bg_width = 0
    full_bg_height = 0

    for screen_info in screen_infos:
        full_bg_width = max(full_bg_width, screen_info['width'] + screen_info['x_org'])
        full_bg_height = max(full_bg_height, screen_info['height'] + screen_info['y_org'])

    return (full_bg_width, full_bg_height)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Set a background image separately for each monitor on a dual head setup. It creates a temporary file (usually in /tmp/), which is used as a background image.')
    parser.add_argument('-s', '--set-program', default='Esetroot {0}', help='the tool used for setting the composited background image. Default is "Esetroot {0}", where {0} will be substituted with the path of the composited background image', nargs=1)
    parser.add_argument('first_image', help='the image for the first screen')
    parser.add_argument('second_image', help='the image for the second screen')

    args = parser.parse_args()

    left_bg_image = PythonMagick.Image(args.first_image)
    right_bg_image = PythonMagick.Image(args.second_image)

    screen_infos = xinerama_query_screens()

    (full_bg_width, full_bg_height) = get_full_bg_size(screen_infos)
    full_bg_image = PythonMagick.Image(
            PythonMagick.Geometry(full_bg_width, full_bg_height),
            PythonMagick.Color("black"))

    for (screen_info, bg_image) in zip(screen_infos, [left_bg_image, right_bg_image]):
        stretch_and_center_image_to_screen(bg_image, screen_info)

        full_bg_image.composite(
                bg_image,
                PythonMagick.Geometry(
                    screen_info['width'],
                    screen_info['height'],
                    screen_info['x_org'],
                    screen_info['y_org']))

    full_bg_file = tempfile.mktemp('.png')
    full_bg_image.write(full_bg_file)
    os.system(args.set_program.format(full_bg_file))
