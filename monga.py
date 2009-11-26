#!/usr/bin/env python

from pymongo import Connection
from collection import Collection
from exc import ConnectionError
from utils import dump_config

class MongoDB(object):
    '''Interface adapter buat interaksi dengan Mongo DB
    '''
    
    def __init__(self,db_name,
                 user_name,
                 user_pass,
                 host,
                 port,
                 config={}
                 ):
        '''params:
            db_name: database name.
            user_name: user name (optional).
            user_pass: authority with password (optional if necessary).
            host: host where mongod alive.
            port: post.
            config: configuration of FMA.
        '''
        
        self._connected=False
        
        try:
            self._cn = Connection(host,port)
            self._db = self._cn[db_name]
        except Exception, e:
            print 'ERROR: ', e
            self._last_error = e
            return
        
        self._connected = True
        
        for x in ('nometaname','notypeknown'):
            if x not in config:
                config[x] = False
        
        self.config = config
        
    @property
    def connected(self):
        return self._connected
    
    @property
    def last_error(self):
        return self._last_error
        
    def __del__(self):
        
        del self._db
        del self._cn
        
    def col(self, doctype, echo=False):
        
        if not self.connected:
            raise ConnectionError, "mongo db not connected"
        
        return Collection(self, doctype, echo=echo)
        
    def set_db(self,db_name):
        
        if not self.connected: return None
        
        self._db = self._cn[db_name]
        

    
def monga_from_config( config, prefix, mongaconf ):
    '''Load monga instance from config preset.
    helper for Plylons. format = Pylons configuration file.
    '''
    kwargs = dump_config( config, prefix)
    kwargs['config'] = mongaconf
    return MongoDB( **kwargs )
