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
