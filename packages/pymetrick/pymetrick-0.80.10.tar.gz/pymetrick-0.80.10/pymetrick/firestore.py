#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
# sin bytecode
sys.dont_write_bytecode = True
import os
import logging
import logging.handlers
import requests

import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials, firestore
from firebase_admin import storage
from firebase_admin import exceptions
#from google.oauth2 import service_account

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

if 'LD_LIBRARY_PATH' in list(os.environ.keys()):
    # CGI environment
    sys.stdout = sys.stderr
    logging.basicConfig(stream = sys.stderr, level=LOG_LEVEL, format='%(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s')
else:
    # not CGI environment
    logging.basicConfig(stream=sys.stderr)
    hdlr = logging.handlers.RotatingFileHandler(filename=LOG_FILENAME+'.log',mode='a', encoding='utf-8', maxBytes=1048576, backupCount=3)
    formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s')
    hdlr.setFormatter(formatter)
    LOG.addHandler(hdlr)
    LOG.setLevel(LOG_LEVEL)


_DEFAULT_TIMEOUT = 60

BUCKET_NAME   = '****.appspot.com'
BUCKET_FOLDER = '/b/****.appspot.com/o'
LOCAL_FOLDER  = 'c:/****'
GOOGLE_CERTIFICATE = "certificates/****-firebase.json"

class GStorage(object):
    def __init__(self, *args, **kwargs):
        try:
            self.bucketName = BUCKET_NAME
            self.bucketFolder = BUCKET_FOLDER
            self.localFolder= LOCAL_FOLDER
            cred = credentials.Certificate(GOOGLE_CERTIFICATE)
            firebase_admin.initialize_app(cred, {'storageBucket': self.bucketName})
            self.bucket = storage.bucket() # return google.cloud.storage.Bucket
           
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))


    def file_upload(self,source_file_name, destination_blob_name):
        """Uploads a file to the bucket."""
        # source_file_name = "local/path/to/file"
        # destination_blob_name = "storage-object-name"
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)
            blob.make_public()
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))
            
    def file_download(self,source_blob_name, destination_file_name):
        """Downloads a blob from the bucket.
        fix requests >= 2.18.0
        """
        # source_blob_name = "storage-object-name"
        # destination_file_name = "local/path/to/file"
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def file_delete(self,blob_name):
        """Deletes a blob from the bucket."""
        # blob_name = "your-object-name"
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def file_rename(self,blob_name, new_name):
        """Renames a blob."""
        # blob_name = "your-object-name"
        # new_name = "new-object-name"
        try:
            blob = self.bucket.blob(blob_name)
            new_blob = self.bucket.rename_blob(blob, new_name)
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))
        

    def list_blobs(self):
        """Lists all the blobs in the bucket."""
        try:
            fileList = []
            if self.bucket.exists():
                files = self.bucket.list_blobs()
                fileList = [file.name for file in files if '.' in file.name]
            return fileList
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))
        
        
    def metadata(self,blob_name):
        """Prints out a blob's metadata."""
        # blob_name = 'your-object-name'
        try:
            blob = self.bucket.get_blob(blob_name).metadata
            for n in blob.keys():
                print("{0} {1}".format(n,blob[n]))
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

 

class GFirestore(object):
    '''
       @parameters
       cert_file :  json file with firebase cert
       batch     :  operations in batch mode


    '''
    def __init__(self, *args, **kwargs):
        try:

            if kwargs.get('cert_file'):
                json_cert = kwargs['cert_file']
            else:
                json_cert = GOOGLE_CERTIFICATE

            # operaciones por lotes o batch
            if kwargs.get('batch') and kwargs['batch']:
                self.batch = True
                LOG.debug('BATCH TRUE')
            else:
                self.batch = False
                
            cred = credentials.Certificate(json_cert)
            firebase_admin.initialize_app(cred)

            self.db = firestore.client()   # return google.cloud.firestore.Firestore object

        except Exception as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))


    def post(self, collection=None, document=dict()):
        self.put(collection=collection, document=document)
        
    def put(self, collection=None, document=dict()):
        """
           @parameters
           collection :  collection name <str>
           document :  <dict> with { 'document_key': { data_dict ...}, }
        """
        try:
            if collection and isinstance(document,(dict,)):

                if self.batch:
                    _batch = self.db.batch()

                for n in document.keys():
                    doc_ref = self.db.collection(u'{0}'.format(collection)).document(u'{0}'.format(n))
                    if self.batch:
                        _batch.set(doc_ref, document[n])
                    else:
                        doc_ref.set(document[n])

                if self.batch:
                    # Commit the batch
                    _batch.commit()
                    # ERROR:firestore:<Quota exceeded.> in line 313 !!!

        except Exception as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))
    
    def get(self, collection=None, document=list()):
        """
           @parameters
           collection :  collection name <str>
           document :  <list> with [ 'document_key' , ...]
        """
        try:
            if collection and isinstance(document,(list,tuple,)):
                _documents = dict()
                if len(document)>0:
                    for n in document:
                        doc_ref = self.db.collection(u"""{0}""".format(collection)).document(u"""{0}""".format(n))
                        doc = doc_ref.get()
                        _documents[n] = doc.to_dict()
                else:
                    # obtener objetos por seleccion
                    '''
                    docs = self.db.collection(u'users').where(u'born', u'==', 1815).stream()
                    for doc in docs:
                        print(u'{} => {}'.format(doc.id, doc.to_dict()))
                    '''
                    # todos los documentos de una coleccion
                    docs = self.db.collection(u"""{0}""".format(collection)).stream()
                    for doc in docs:
                        print(u'{} => {}'.format(doc.id, doc.to_dict()))

        except Exception as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))


    def delete(self, collection=None, document=list()):
        """
           @parameters
           collection :  collection name <str>
           document :  <list> with [ 'document_key' , ...]
        """
        try:
            if collection and isinstance(document,(list,tuple,)):

                if self.batch:
                    _batch = self.db.batch()
                
                _documents = dict()
                if len(document)>0:
                    for n in document:
                        doc_ref = self.db.collection(u'{0}'.format(collection)).document(u'{0}'.format(n))
                        if self.batch:
                            _batch.delete(doc_ref)
                        else:
                            doc = doc_ref.delete()
                if self.batch:
                    # Commit the batch
                    _batch.commit()
                            
        except Exception as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))


AUTHORIZED_KEYS = ['email',
                   'phone_number',
                   'email_verified',
                   'password',
                   'display_name',
                   'photo_url',
                   'disabled',
                   'app']

class GAuth(object):
    def __init__(self, *args, **kwargs):
        try:
            self.bucketName = BUCKET_NAME
            self.bucketFolder = BUCKET_FOLDER
            cred = credentials.Certificate(GOOGLE_CERTIFICATE)
            firebase_admin.initialize_app(cred, {'storageBucket': self.bucketName})

        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def create_user(self,kwargs):
        """Upload files to GCP bucket.
        uid 	string 	El uid que se asignará al usuario recién creado. Debe ser una string que contenga entre 1 y 128 caracteres. Si no se proporciona, se generará automáticamente un uid aleatorio.
        email 	string 	El correo electrónico principal del usuario. Debe ser una dirección de correo electrónico válida.
        emailVerified 	booleano 	Indica si se verificó el correo electrónico principal del usuario. Si no se proporciona, el valor predeterminado es false.
        phoneNumber 	string 	El número de teléfono principal del usuario. Debe ser un número de teléfono válido que cumpla con las especificaciones E.164.
        password 	string 	La contraseña del usuario, sin encriptación. Debe tener al menos seis caracteres.
        displayName 	string 	El nombre visible del usuario.
        photoURL 	string 	La URL de la foto del usuario.
        disabled 	booleano 	Si el usuario está inhabilitado o no. true indica que está inhabilitado; false indica que está habilitado. Si no se proporciona, el valor predeterminado es false. 
        app:            An App instance (optional)
        """
        # uid se crea de forma aleatoria
        try:
            user_auth = dict()
            print(kwargs)
            print(**kwargs)
            for key in kwargs.keys():
                if key in AUTHORIZED_KEYS and kwargs[key] is not None:
                    user_auth[key] = kwargs[key]
            if not user_auth.get('email_verified',False):
                user_auth['email_verified'] = False
            if not user_auth.get('disabled',False):
                user_auth['disabled'] = False
            print(**user_auth)

            ''' si deseo crear mi usuario con uid propio 
            
            user = auth.create_user(
                uid='some-uid', email='user@example.com', phone_number='+15555550100')
            print('Sucessfully created new user: {0}'.format(user.uid))
            '''

        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def verify_email(self,email):
        """email verify
           @parameter
               email
           @return
               The email verification link created by the API. Send email to user with link
        """
        try:
            email_verify_link = auth.generate_email_verification_link(email, action_code_settings=None, app=None)
            return(email_verify_link)
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def reset_password(self,email):
        """password reset
           @parameter
               email
           @return
               The email verification link created by the API. Send email to user with link
        """
        try:
            reset_password_link = auth.generate_password_reset_link(email, action_code_settings=None, app=None)
            return(reset_password_link)
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def update_user(self):
        try:
            user = auth.update_user(
                uid,
                email='user@example.com',
                phone_number='+15555550100',
                email_verified=True,
                password='newPassword',
                display_name='John Doe',
                photo_url='http://www.example.com/12345678/photo.png',
                disabled=True)
        except exceptions.ValueError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def delete_user(self, uid):
        try:        
            auth.delete_user(uid, app=None)
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def get_user(self,**kwargs):
        """
           @parameters
               uid || email || phone
           @return
               UserRecord
        """
        try:
            user_record = None
            if kwargs.get('uid',None):
                # Gets the user data corresponding to the specified user ID
                user_record = auth.get_user(kwargs['uid'])
            elif kwargs.get('email',None):
                # Gets the user data corresponding to the specified user email
                user_record = auth.get_user_by_email(kwargs['email'])
            elif kwargs.get('phone',None):
                # Gets the user data corresponding to the specified phone number.
                user_record = auth.get_user_by_phone_number(kwargs['phone'])
            print(user_record.to_dict())
            print(user_record.uid)
            print(user_record.email_verified)
            return user_record.uid
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))

    def user_list(self):
        # Start listing users from the beginning, 1000 at a time.
        try:
            """
            page_token – A non-empty page token string, which indicates the starting point of the page (optional). Defaults to None, which will retrieve the first page of users.
            max_results – A positive integer indicating the maximum number of users to include in the returned page (optional). Defaults to 1000, which is also the maximum number allowed.
            app – An App instance (optional).
            """
            page = auth.list_users(page_token=None, max_results=1000, app=None)
            while page:
                for user in page.users:
                    print('User: ' + user.uid)
                # Get next batch of users.
                page = page.get_next_page()

            # Iterate through all users. This will still retrieve users in batches,
            # buffering no more than 1000 users in memory at a time.
            """
            for user in auth.list_users().iterate_all():
                print('User: ' + user.uid)
            """
        except exceptions.FirebaseError as e:
            if hasattr(e, 'message'):
                LOG.error('<%s> in line %s !!!' % (e.message,format(sys.exc_info()[-1].tb_lineno)))
            else:
                LOG.error('<%s> in line %s !!!' % (e,format(sys.exc_info()[-1].tb_lineno)))



if __name__ == "__main__":

    print ('''copyright {0}'''.format( __copyright__))
    print ('''license {0}'''.format( __license__))
    print ('''version {0}'''.format( __version__))
    if len(sys.argv) < 2:
        sys.stderr.write("For help use -h o --help")
    elif sys.argv[1]=='-h' or sys.argv[1]=='--help':
        print (''' Google Firestore data ''')
