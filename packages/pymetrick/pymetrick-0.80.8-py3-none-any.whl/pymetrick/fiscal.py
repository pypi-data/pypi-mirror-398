def calcula_dc(secuencia):
    """Calcula el dígito de control de una CCC.
    Recibe una lista con 10 numeros enteros y devuelve el DC
    correspondiente"""

    pesos = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6]
    aux = []
    for i in range(10):
        aux.append(secuencia[i]*pesos[i])
    resto = 11 - sum(aux)%11
    if resto == 10:
        return 1
    elif resto == 11:
        return 0
    else:
        return resto


import random
from core import _random_words

sociedades = ('SL', 'SA', 'SLU', 'CB', '')
_random_sociedades = lambda:random.choice(sociedades)

def genera_NIF():
    """
    El nif corresponde a un número de identificación para
    individuos, se compone de un número (el DNI) seguido
    por una letra
    """
    num = random.randint(1000000, 100000000)
    nif_control = 'TRWAGMYFPDXBNJZSQVHLCKE'
    checksum = nif_control[int(num)%23]
    return "%s%s" % (num, checksum)

def genera_CIF():
    """
    El CIF se corresponde con el identificador para las
    empresas, es de la forma letra+numero

    http://es.wikipedia.org/wiki/C%C3%B3digo_de_identificaci%C3%B3n_fiscal

    A la hora de generar los CIF priorizaremos las sociedadeS
    anónimas y las limitadas.

    """

    def cif_get_checksum(number, tipo):
        cif_control = 'JABCDEFGHI'
        s1 = sum([int(digit) for pos, digit in enumerate(number) if int(pos) % 2])
        s2 = sum([sum([int(unit) for unit in str(int(digit) * 2)]) for pos, digit in enumerate(number) if not int(pos) % 2])
        num =  (10 - ((s1 + s2) % 10)) % 10
        if tipo in ['A', 'B', 'E', 'H']:
            return num
        else:
            return cif_control[num]
    cifs_habituales = 'AB'
    cif_types = 'CDEFGHKLMNPQS'
    tipo = random.randint(0, 100)
    # cambiamos de distribución uniforme a distribución por peso
    letra = random.choice(cifs_habituales) if tipo < 80 else \
        random.choice(cif_types)
    numero = "%02d%05d" % (random.randint(1, 100),
        random.randint(1000, 100000))
    chk = cif_get_checksum(numero, letra)
    return "%(letra)s%(numero)s%(control)s" % \
        {'letra': letra,
         'numero': numero,
         'control': chk
         }

def nombre_empresa():
    """
    Devuelve una tupla compuesta por el nombre
    de la empresa y su tipo
    """
    num = random.randrange(2, 4)
    empresa = _random_words(num).upper()
    empesa_full = empresa
    x = _random_sociedades()
    return empresa, x



if __name__=='__main__':
    pass
    '''
    print "CIFs"
    print "===="
    for i in range(0, 10):
        print genera_CIF()
    print

    print "NIFs"
    print "===="
    for i in range(0, 10):
        print genera_NIF()

    print
    print "EMPRESAS"
    print "========"
    for i in range(0, 10):
        print " ".join(nombre_empresa())

    # Para cuenta bancaria

    ccc = raw_input("Introduce el CCC: ").split('-')
    entidadyoficina = [0, 0]
    for i in range(2):
        for j in range(4):
            entidadyoficina.append(int(ccc[i][j]))
    cuenta = []
    for i in range(10):
        cuenta.append(int(ccc[3][i]))
    dc = str(calcula_dc(entidadyoficina))+str(calcula_dc(cuenta))
    if dc == ccc[2]:
        print 'CCC verificado'
    else:
        print 'Hay un error en el CCC'
    '''