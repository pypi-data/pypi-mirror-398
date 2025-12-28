#!/usr/bin/python
# -*- coding: utf-8 *-*

"""Modulo para gestionar datos en SQLite"""

from pymetrick import version
__author__ = version.__author__
__copyright__ = version.__copyright__
__license__ = version.__license__
__version__ = version.__version__
__date__ = '2012-09-21'
__credits__ = ''
__text__ = 'Gestion de datos en BBDD SQLite'
__file__ = 'db_sqlite.py'

#--- CHANGES ------------------------------------------------------------------
# 2012-09-21 v0.01 PL: - First version

import os
import sys
import logging
import logging.handlers

try:
    import sqlite3 as lite
except ImportError:
    # If MySQLdb isn't available this module won't actually be useable,
    # but we want it to at least be importable (mainly for readthedocs.org,
    # which has limitations on third-party modules)
    lite = None

import sys, os, re

# Version PY
PY2 = True if sys.version[:1] == '2' else False;
PY3 = True if sys.version[:1] == '3' else False;

if PY2:
    # python3 chr & python2 unichr
    chr = unichr

if PY3:
    long = int

class Db_SQLite:
    _db_name_ = ''
    db = ''
    cursor = ''
    rows = ''
    _error_ = ''

    def __init__(self, db_name=None):
        """Abrir acceso a MySQL"""
        self._db_name_ = db_name


    def conecta_db(self):
        """Crear una conexión con la base de datos"""
        global db
        global _db_name_
        try:
            if self._db_name_:
                self.db = lite.connect(self._db_name_)
            else:
                self.db = lite.connect(':memory:', check_same_thread = False)
        except lite.Error as e:
            print ("Error %s:" % e.args[0])
            sys.exit(1)

    def desconecta_db(self):
        """Desconectar la base de datos"""
        global db
        if self.db:
            self.db.close()

    def abre_cursor(self):
        """Abrir un cursor"""
        global cursor
        self.cursor = self.db.cursor()

    def cierra_cursor(self):
        """Cerrar cursor"""
        global cursor
        self.cursor.close()

    def ejecuta_consulta(self, query='', values=''):
        """Ejecutar una consulta"""
        global cursor
        global _error_
        global db
        self._error_ = ''
        try:
            if query:
                query.strip()
                '''Comprobar si final con ; '''
                if query[-1:]!=';':
                    query += ';'
                    print (query)
                '''Si tiene valores para INSERT'''
                if type(values).__name__=='tuple' and query.find('?')>0 and query[0:6].upper()=='INSERT':
                    if type(values[0]).__name__=='tuple':
                        self.cursor.executemany(query, values)
                    else:
                        self.cursor.execute(query, values)
                elif type(values).__name__=='tuple' and query.find('?')>0 and query[0:6].upper()=='UPDATE':
                    if type(values[0]).__name__=='tuple':
                        for t in values:
                            self.cursor.execute(query, t)
                    else:
                        self.cursor.execute(query, values)
                else:
                    if type(values).__name__=='tuple':
                        _sql_ = (query % values)
                        self.cursor.execute(_sql_)
                    else:
                        self.cursor.execute(query)
        except lite.Error as e:
            if self.db:
                self._error_ = 'error'
                self.db.rollback()

    def selecciona_datos(self):
        """Traer todos los registros"""
        global cursor
        global rows
        self.rows = self.cursor.fetchall()

    def confirma(self):
        """Enviar commit a la base de datos"""
        global db
        self.db.commit()

    def ejecuta(self, query='', values=''):
        """Compilar todos los procesos"""
        global rows
        global _error_
        if query:
            self.conecta_db()
            self.abre_cursor()
            self.ejecuta_consulta(query, values)
            if query[0:6].upper()=='INSERT' or query[0:6].upper()=='UPDATE' or query[0:6].upper()=='DELETE':
                self.confirma()
            if query[0:6].upper()=='SELECT':
                self.selecciona_datos()
            self.cierra_cursor()
            self.desconecta_db()
            if query[0:6].upper()=='SELECT':
                if not self._error_:
                    return self.rows
                else:
                    return self._error_

    def crea_tabla(self, db_table='', values=''):
        """Crear tablas"""
        self.sql = ('''CREATE TABLE %s (%s)''' % (db_table,values))
        self.ejecutar_consulta(self.sql)

    def data_type(self):
        """Tipo de datos"""
        type = (('INTEGER','INT,INTEGER,TINYINT,SMALLINT,MEDIUMMINT,BIGINT,UNSIGNED BIG INT,INT2,INT8'),
                ('TEXT','CHARACTER,VARCHAR,VARYING CHARACTER,NCHAR,NATIVE CHARACTER,NVARCHAR,TEXT,CLOB'),
                ('NONE','BLOB'),
                ('REAL','REAL,DOUBLE,DOUBLE PRECISION,FLOAT'),
                ('NUMERIC','NUMERIC,DECIMAL,BOOLEAN,DATE,DATETIME')
                ('DATE','DATE,DATETIME')
                ('TIME','TIME')
                ('DATETIME','DATETIME')
                ('JULIANDAY','NUMERIC,DECIMAL,BOOLEAN,DATE,DATETIME') )

        '''
            %d day of month: 00
            %f fractional seconds: SS.SSS
            %H hour: 00-24
            %j day of year: 001-366
            %J Julian day number
            %m month: 01-12
            %M minute: 00-59
            %s seconds since 1970-01-01
            %S seconds: 00-59
            %w day of week 0-6 with Sunday==0
            %W week of year: 00-53
            %Y year: 0000-9999
            %% %
        '''
    def columnas(self):
        """Obtener nombres de las columnas"""
        self.db.row_factory = lite.Row
        '''cur.execute('SELECT SQLITE_VERSION()') '''
        '''cur.execute('SELECT name FROM sqlite_master;')'''
        '''cur.execute('SELECT * FROM sqlite_master;')
           (u'table', u'Cars', u'Cars', 2, u'CREATE TABLE Cars(Id INT, Name TEXT, Price INT)')
           (u'table', u'Friends', u'Friends', 3, u'CREATE TABLE Friends(Id INTEGER PRIMARY KEY, Name TEXT)')
        '''
        '''Foreign key

           conn.execute('pragma foreign_keys=ON')

           CREATE TABLE track(
           trackid     INTEGER,
           trackname   TEXT,
           trackartist INTEGER,
           FOREIGN KEY(trackartist) REFERENCES artist(artistid)
           );
        '''
        '''Index
           CREATE TABLE parent(a PRIMARY KEY, b UNIQUE, c, d, e, f);
           CREATE UNIQUE INDEX i1 ON parent(c, d);

           CREATE TABLE parent2(a, b, PRIMARY KEY(a,b));

           CREATE TABLE album(
           albumartist TEXT,
           albumname TEXT,
           albumcover BINARY,
           PRIMARY KEY(albumartist, albumname)
           );

           CREATE TABLE song(
           songid     INTEGER,
           songartist TEXT,
           songalbum TEXT,
           songname   TEXT,
           FOREIGN KEY(songartist, songalbum) REFERENCES album(albumartist, albumname)
           );

           CREATE TABLE artist(
           artistid    INTEGER PRIMARY KEY,
           artistname  TEXT
           );
           CREATE TABLE track(
           trackid     INTEGER,
           trackname   TEXT,
           trackartist INTEGER REFERENCES artist(artistid) ON UPDATE CASCADE
           );

           FOREIGN KEY(foreign_key_field) REFERENCES parent_table_name(parent_key_field) ON DELETE CASCADE ON UPDATE CASCADE );

           id integer primary key autoincrement, name text, city text, state text, zip integer, acquired_by text, close_date date, updated_date date
        '''


def SQLite2MySQL(sqlite_file=''):
    '''Transformar un fichero dump de sqlite a mysql'''
    _file = ''
    linea = ''
    f = ''
    try:
        '''Comprueba si existe el fichero sqlite .db para hacer un .dump o continuar'''
        if sqlite_file and sqlite_file[-2:]=='db':
            os.system(('sqlite3 %s .dump' % sqlite_file))
            sqlite_file = sqlite_file[0:-2]+'sql'

        _file = sqlite_file.lower()
        if _file and _file[-3:]=='sql' and os.path.isfile(_file):
            f1 = open(_file,"r")
            f2 = open(_file[0:-4]+'_mysql'+_file[-4:],"w")
            while True:
                linea = ''+f1.readline()
                linea = linea.replace('\xef\xbb\xbf','')
                if linea.__len__()==0:
                    '''No existen datos y finaliza el proceso si supera 2 lineas en blanco'''
                    _empty += 1
                    if _empty > 1:
                        _empty = 0
                        break
                else:
                    _empty = 0

                    if (
                        linea.startswith("PRAGMA") or
                        linea.startswith("BEGIN TRANSACTION;") or
                        linea.startswith("COMMIT;") or
                        linea.startswith("DELETE FROM sqlite_sequence;") or
                        linea.startswith("INSERT INTO \"sqlite_sequence\"")
                        ):
                        linea = ''
                    else:
                        linea = linea.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
                        linea = linea.replace("INTEGER PRIMARY KEY", "INTEGER AUTO_INCREMENT PRIMARY KEY")
                        linea = linea.replace("AUTOINCREMENT", "AUTO_INCREMENT")
                        linea = linea.replace("CONSTRAINT []", "")
                        linea = linea.replace("TEXT DEFAULT ('')", "TEXT")
                        linea = linea.replace("DEFAULT 't'", "DEFAULT '1'")
                        linea = linea.replace("DEFAULT 'f'", "DEFAULT '0'")
                        linea = linea.replace("DEFAULT (1)", "DEFAULT '1'")
                        linea = linea.replace("DEFAULT (-1)", "DEFAULT '-1'")
                        linea = linea.replace("DEFAULT (0)", "DEFAULT '0'")
                        linea = linea.replace("DEFAULT 0", "DEFAULT '0'")
                        linea = linea.replace("DEFAULT ('')", "DEFAULT ''")
                        linea = linea.replace("DEFAULT('')", "DEFAULT ''")
                        linea = linea.replace("INTEGER DEFAULT (strftime('%s','now'))", "timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                        linea = linea.replace(",'t'", ",'1'")
                        linea = linea.replace(",'f'", ",'0'")
                        linea_campos = re.findall(r',\s+\w+\s+',linea)
                        for i in linea_campos:
                            i = i.replace(',','').strip()
                            linea = linea.replace(i,("`%s`" % i))
                        linea = linea.replace("[", "`").replace("]","`")
                        linea = linea.replace("TEXT", "TEXT COLLATE utf8_spanish_ci")

                        in_string = False
                        newLinea = ""

                        for c in linea:
                            if not in_string:
                                if c == "'":
                                    in_string = True
                                elif c == '"':
                                    newLinea = newLinea + '`'
                                    continue
                            elif c == "'":
                                in_string = False
                            newLinea = newLinea + c
                        if newLinea.__len__():
                            f2.write(newLinea)
    except Exception as e:
        tb = sys.exc_info()[2]
        print ('Error <%s> en linea %s !!!' % (str(e),tb.tb_lineno))
        return False
    finally:
        if _file and os.path.isfile(_file):
            f1.close()
            f2.close()
        return True

