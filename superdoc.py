#@TODO: finish this code
from doc import Doc
from pymongo.dbref import DBRef
from nested import Nested
from antypes import *
from exc import *
from orm import *

import types


class SuperDoc(Doc):
    
    def __init__(self, _db=None, **datas):
        
        self.__dict__['_data'] = Nested()
        
        _has_opt = hasattr(self,"_opt")
        
        if _has_opt:
            self.__dict__['_opt'] = self._opt
            if self._opt.get('strict') == True:
                for k in datas.keys():
                    if not self.__has_entryname(k):
                        raise SuperDocError, "`%s` is strict model. Cannot assign entryname for `%s`" % ( self.__class__.__name__,k )
            
        
        for k, v in datas.iteritems():
            self.__setattr__( k, v )
            
        Doc.__init__(self, datas)
        
        self.__sanitize()
        
        
        # buat metaname untuk modelnya
        setattr( self.__dict__['_data'], '_metaname_', self.__class__.__name__ )
        
        if _has_opt:
            if not self._saved() and self._opt.has_key('default'):
                for k, v in self._opt['default'].iteritems():
                    if hasattr(self,k):
                        if getattr(self.__dict__['_data'], k) is None:
                            if type( v ) in [types.FunctionType, types.BuiltinFunctionType]:
                                setattr( self.__dict__['_data'], k, apply( v ) )
                            else:
                                setattr( self.__dict__['_data'], k, v )
                    else:
                        raise SuperDocError, \
                            '%s has no attribute name %s for default value assignment' \
                            % (self.__class__.__name__,k)


        for x in filter( lambda x: type(getattr(self,x)) == relation, dir(self) ):
            
            _t = getattr(self,x).copy()
            _t._parent_class = self
            
            setattr(self,x,_t)
            
        setattr(self,'_db',_db)
        
        self.__dict__['_modified_childs'] = []
        
    def bind_db(self, db):
        self._db = db

    def __sanitize(self):
        
        # map class atribute based user definition to _data container collection
        _attrs = filter( lambda x: type(getattr(self.__class__,x)) == types.TypeType and x not in ['__class__'], dir(self.__class__) )

        for x in _attrs:

            y = x
            if type(getattr(self,x)) != relation:
                
                if not x.startswith('_x_'):

                    setattr(self.__class__, '_x_%s' % x, getattr(self.__class__, x) )
                    delattr(self.__class__, x)

                else:

                    y = x[3:]
            
            if not hasattr(self.__dict__['_data'],y):
                setattr(self.__dict__['_data'],y,None)
            
    def validate(self):
        
        if hasattr(self, 'req'):
            for x in self.req:
                
                if hasattr(self,x):
                    if getattr(self,x) is None:
                        raise SuperDocError, "%s require value for %s" % (self.__class__.__name__,x)
                else:
                    raise SuperDocError, "%s has no required value for %s" % (self.__class__.__name__,x)

        return 'OK'

    def save(self):

        self.validate()
        
        if self._db is None:
            raise SuperDocError, "This res not binded to database. Try to bind it first use bind_db(<db>)"

        Doc.save(self)
        
        global RELATION_RECURSION_DEEP, MAX_RECURSION_DEEP
        
        RELATION_RECURSION_DEEP += 1
        
        if RELATION_RECURSION_DEEP < MAX_RECURSION_DEEP:
            
            self._call_relation_attr( '_update_hash' )
            self._call_relation_attr( '_save' )
            
            RELATION_RECURSION_DEEP -= 1
        else:
            raise SuperDocError, "Recursion limit reached, max %d" % MAX_RECURSION_DEEP
        
    

    def _set_relation_attr(self, attr, val):

        for x in filter( lambda x: type(getattr(self.__class__,x)) == relation, dir(self.__class__) ):
            
            t = getattr(self,x)
            
            setattr(t.__class__, attr, val)
            
            setattr(self.__class__, x, t)


    def _call_relation_attr(self, attr, *args, **kwargs):

        for x in filter( lambda x: type(getattr(self.__class__,x)) == relation, dir(self.__class__) ):
            
            t = getattr(self,x)
            
            if hasattr(t, attr):
            
                getattr(t,attr)( *args, **kwargs )
                

    def __getitem__(self, k):
        return getattr(self.__dict__['_data'], k)
        
    
    def __getattr__(self, k):
        
        if hasattr(self.__dict__['_data'], k):
            
            v = getattr(self.__dict__['_data'], k)
            
            if ( type( v ) == relation ):
                return getattr( v, k )
                
            
        return Doc.__getattr__(self, k)
    
    
    def __has_entryname(self, name):
        if name in ['_db','_id','_metaname_']:
            return True
        return (hasattr(self.__class__, name) and type(getattr(self.__class__, name)) in [relation, types.TypeType]) or hasattr(self.__class__, '_x_%s' % name)
        
        
    def __setattr__(self, k, v):
        
        
        if self.__dict__.has_key('_opt') and self.__dict__['_opt'].get('strict') == True:
            if self.__has_entryname( k ) == False:
                raise SuperDocError, "`%s` is strict model. Cannot assign entryname for `%s`" % ( self.__class__.__name__,k )
        
        if hasattr( self.__class__, '_x_%s' % k ):
            typedata = getattr( self.__class__, '_x_%s' % k )
            #v = type(v)==str and unicode(v) or v
            if typedata != type(v) and type(v) is not types.NoneType:
                # try to convert it if possible
                try:
                    v = typedata(v)
                except:
                    raise SuperDocError, "mismatch data type `%s`=%s and `%s`=%s" % (k,typedata,v,type(v))
            
        Doc.__setattr__(self, k , v)


    def __delitem__(self, k):
        delattr(self.__dict__['_data'], k)

    
    def _saved(self):
        return hasattr(self.__dict__['_data'],'_id') and self._id is not None
        
    
    def _changed(self):
        
        return not self._saved() or len(self.__dict__['_modified_childs']) > 0
        
        
    def delete(self):
        
        # hapus juga semua anak yg menjadi relasi di dalamnya
        # yang diset sebagai cascade=delete
        self._call_relation_attr('_delete_cascade')
        
        Doc.delete(self)
    

    def __repr__(self):
        
        if self._saved():
            return '<SuperDoc(id=%s)>' % self.__dict__['_data']._id
        else:
            return '<SuperDoc(id=Unsaved)>'





