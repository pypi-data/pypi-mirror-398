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

import sys
# sin bytecode
sys.dont_write_bytecode = True

from pymetrick.py3k import PY3K, basestring, unicode

# fpdf php helpers:

def substr(s, start, length=-1):
    if length < 0:
        length=len(s)-start
    return s[start:start+length]

def sprintf(fmt, *args): return fmt % args

def print_r(array):
    if not isinstance(array, dict):
        array = dict([(k, k) for k in array])
    for k, v in array.items():
        print("[%s] => %s " % (k, v))
        
def UTF8ToUTF16BE(instr, setbom=True):
    "Converts UTF-8 strings to UTF16-BE."
    outstr = "".encode()
    if (setbom):
        outstr += "\xFE\xFF".encode("latin9")
    if not isinstance(instr, unicode):
        instr = instr.decode('UTF-8')
    outstr += instr.encode('UTF-16BE')
    # convert bytes back to fake unicode string until PEP461-like is implemented
    if PY3K:
        outstr = outstr.decode("latin9")
    return outstr

def UTF8StringToArray(instr):
    "Converts UTF-8 strings to codepoints array"
    return [ord(c) for c in instr]

# ttfints php helpers:    

def die(msg):
    raise RuntimeError(msg)
    
def str_repeat(s, count):
    return s * count
    
def str_pad(s, pad_length=0, pad_char= " ", pad_type= +1 ):
    if pad_type<0: # pad left
        return s.rjust(pad_length, pad_char)
    elif pad_type>0: # pad right
        return s.ljust(pad_length, pad_char)
    else: # pad both
        return s.center(pad_length, pad_char)

strlen = count = lambda s: len(s)
