#!/usr/bin/env python

from pymongo import Connection
from collection import Collection
from exc import ConnectionError

class MongoDB(object):
    '''Interface adapter buat interaksi dengan Mongo DB
    '''
    
    def __init__(self,db_name,user_name,user_pass,host,port):
        
        self._connected=False
        
        try:
            self._cn = Connection(host,port)
            self._db = self._cn[db_name]
        except Exception, e:
            print 'ERROR: ', e
            self._last_error = e
            return
        
        self._connected = True
        
        
    @property
    def connected(self):
        return self._connected
    
    @property
    def last_error(self):
        return self._last_error
        
    def __del__(self):
        
        del self._db
        del self._cn
        
    def col(self, doctype):
        
        if not self.connected:
            raise ConnectionError, "mongo db not connected"
        
        return Collection(self._db, doctype)
        
    def set_db(self,db_name):
        
        if not self.connected: return None
        
        self._db = self._cn[db_name]
        