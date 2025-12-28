#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ****************************************************************************
# * Software: FPDF for python                                                *
# * Version:  1.7.1a                                                          *
# * Date:     2010-09-10                                                     *
# * Last update: 2019-01-01                                                  *
# * License:  LGPL v3.0                                                      *
# *                                                                          *
# * Original Author (PHP):  Olivier PLATHEY 2004-12-31                       *
# * Ported to Python 2.4 by Max (maxpat78@yahoo.it) on 2006-05               *
# * Maintainer:  Mariano Reingart (reingart@gmail.com) et al since 2008 est. *
# * NOTE: 'I' and 'D' destinations are disabled, and simply print to STDOUT  *
# * Updated only for PYMETRICK 01/01/2019 by javtamvi@pymetrick.org          * 
# ****************************************************************************

"Special module to handle differences between Python 2 and 3 versions"

import sys, os
# sin bytecode
sys.dont_write_bytecode = True

PY3K = sys.version_info >= (3, 0)

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from hashlib import md5
except ImportError:
    try:
        from md5 import md5
    except ImportError:
        md5 = None
def hashpath(fn):
    h = md5()
    if PY3K:
        h.update(fn.encode("UTF-8"))
    else:
        h.update(fn)
    return h.hexdigest()

# Check if PIL is available (tries importing both pypi version and corrected or manually installed versions).
# Necessary for JPEG and GIF support.
# TODO: Pillow support
try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None

try:
	from HTMLParser import HTMLParser
except ImportError:
	from html.parser import HTMLParser

if PY3K:
    basestring = str
    unicode = str
    ord = lambda x: x
else:
    basestring = basestring
    unicode = unicode
    ord = ord

import logging
import logging.handlers

'''
DEBUG - debug message
INFO - info message
WARNING - warn message
ERROR - error message
CRITICAL - critical message
'''
LOG_LEVEL_VALUE = {'DEBUG':10,'INFO':20,'WARNING':30,'ERROR':40,'CRITICAL':50}
if str(os.environ.get('PYMETRICK_LOG_LEVEL',None)).upper() in LOG_LEVEL_VALUE:
    LOG_LEVEL = LOG_LEVEL_VALUE[str(os.environ.get('PYMETRICK_LOG_LEVEL')).upper()]
else:
    LOG_LEVEL = 30
LOG_FILENAME = '-'.join([os.path.abspath(__file__).split(os.sep)[len(os.path.abspath(__file__).split(os.sep))-1],])[:-3]
LOG = logging.getLogger(LOG_FILENAME)    

# shortcut to bytes conversion (b prefix)
def b(s):
    if isinstance(s, basestring):
        return s.encode("latin9")
    elif isinstance(s, int):
        if PY3K:
            return bytes([s])       # http://bugs.python.org/issue4588
        else:
            return chr(s)
                      
def exception():
    "Return the current the exception instance currently being handled"
    # this is needed to support Python 2.5 that lacks "as" syntax
    return sys.exc_info()[1]


