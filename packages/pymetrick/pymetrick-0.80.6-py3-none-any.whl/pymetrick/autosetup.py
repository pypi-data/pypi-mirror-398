#!/usr/bin/python
# -*- coding: utf-8 *-*

"""Modulo para gestionar datos en SQLite"""

__author__ = 'Fco.Javier Tamarit V <javtamvi@gmail.com>'
__copyright__ = "Copyright � 2012 Betaksistemas"
__date__ = '2012-09-21'
__version__ = '0.01'
__license__ = 'GPLv3'
__credits__ = ''
__text__ = 'Instalador local de los módulos de PYMETRICK en plataformas windows y linux'
__file__ = 'autosetup.py'

#--- CHANGES ------------------------------------------------------------------
# 2012-09-21 v0.01 PL: - First version

import os
import sys

platform = sys.platform
# Nos entrega la version de python en formato de dict
version = sys.version_info
# Nos entrega el path en forma de list
path = sys.path
d = ''
d_list = list()
for p in path:
    if p.find('site-packages')>0:
        d = p[:p.find('site-packages')+len('site-packages')]
    if p.find('dist-packages')>0:
        d = p[:p.find('dist-packages')+len('dist-packages')]
    # Guarda todos los directorios que contienen site-packages o dist-packages y no repetidos
    if len(d)>0:
        if d not in d_list:
            d_list.append(d)
# Comienza instalacion de paquete
for d in d_list:
    d = d+os.sep
    d = d+'pymetrick'
    if not os.path.isdir(d):
        os.mkdir(d)
    # directorio origen
    source = os.listdir(os.getcwd())
    if platform.startswith('linux'):
        for f in source:
            os.system("cp -f "+os.getcwd()+os.sep+f+" "+d)
            print os.getcwd()+os.sep+f+" "+d
    if platform.startswith('win'):
        for f in source:
            os.system("copy "+os.getcwd()+os.sep+f+" "+d)
