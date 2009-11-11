#@TODO: finish this code
from doc import Doc, reserved_words
from pymongo.dbref import DBRef
from pymongo.objectid import ObjectId
from nested import Nested
from antypes import *
from exc import *
from orm import *

import types


class SuperDoc(Doc):
    '''Advanced document for mongo ORM data model
    '''
    
    def __init__(self, _db=None, **datas):
        
        self._load( _db, **datas )
        self._echo = False
        
        
    def _load(self, _db, **datas):
        
        self.__dict__['_data'] = Nested(datas)
        
        _has_opt = hasattr(self,"_opt")
        
        if _has_opt:
            self.__dict__['_opt'] = self._opt
            if self._opt.get('strict') == True:
                for k in datas.keys():
                    if not self.__has_entryname(k):
                        raise SuperDocError, "`%s` is strict model. Cannot assign entryname for `%s`" % ( self.__class__.__name__,k )
            
        
        for k, v in datas.iteritems():
            self.__setattr__( k, v )
            

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

        setattr(self,'_db',_db)

        for x in filter( lambda x: type(getattr(self,x)) == relation, dir(self) ):
            
            _t = getattr(self,x).copy()
            _t._parent_class = self
            
            setattr(self,x,_t)
            
            if _t._type == 'many-to-many':
                if not hasattr(self, _t._keyrel[0]):
                    setattr( self, _t._keyrel[0], [] ) # reset m2m relation meta list
        

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
        
        # refresh relation state
        self.__map_relation()
        

    #def _set_relation_attr(self, attr, val):
    #
    #    for x in filter( lambda x: type(getattr(self.__class__,x)) == relation, dir(self.__class__) ):
    #        
    #        t = getattr(self,x)
    #        
    #        setattr(t.__class__, attr, val)
    #        
    #        #setattr(self.__class__, x, t)


    def _call_relation_attr(self, attr, *args, **kwargs):

        for x in filter( lambda x: type(getattr(self.__class__,x)) == relation, dir(self.__class__) ):
            
            t = getattr(self,x)
            
            if hasattr(t, attr):
            
                getattr(t,attr)( *args, **kwargs )
                
                
    def refresh(self):
        '''Reload data from database, for keep data up-to-date
        '''
        
        if not hasattr(self, '_id') or self._id is None:
            raise SuperDocError, "Cannot refresh data from db, may unsaved document?"
        
        doc = self._db[self._collection_name].find_one(self._id)
        
        if not doc:
            return False
        
        self._load( self._db, **dictarg(doc) )
        self.__map_relation()
        
        return True
    
    
    def __map_relation(self):
        '''Untuk menge-map relasi dengan cara me-reload semua relasinya
        agar up-to-date dengan db.
        '''
        for x in filter( lambda x: type( getattr(self.__class__,x) ) == relation , dir(self.__class__) ):
            
            rel = getattr( self, x )
            if rel is not None:
                rel._parent_class = self # don't know it is necessary??
                rv = rel.reload()
                if rel._type == 'one-to-one':
                    if type(rv) == types.NoneType:
                        setattr ( self, x, None ) # null it

            else:
                # reload relation
                rel = getattr( self.__class__, x ).copy()
                rel._parent_class = self
                rel.reload()
                setattr( self, x, rel )
    
    
    def __cmp__(self, other):
        if not hasattr( self, '_id') or not hasattr( other, '_id' ):
            return -1
        return cmp( self._id, other._id)


    def __getitem__(self, k):
        return getattr(self.__dict__['_data'], k)
        
    
    def __getattr__(self, k):
        
        if hasattr(self.__dict__['_data'], k):
            
            v = getattr(self.__dict__['_data'], k)
            
            if ( type( v ) == relation ):
                return getattr( v, k )
                
            
        return Doc.__getattr__(self, k)
    
    
    def __has_entryname(self, name):
        if name in ('_db','_id','_metaname_','_parent_class','_echo'): return True
        return (hasattr(self.__class__, name) and type(getattr(self.__class__, name)) in [relation, types.TypeType]) or hasattr(self.__class__, '_x_%s' % name)
        
        
    def __setattr__(self, k, v):
        
        if k in reserved_words:
            return Doc.__setattr__(self, k , v)
        
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
            
        # check if one-to-one relation
        # just map it to pk==fk
        if hasattr(self.__class__,k) and type( getattr(self.__class__,k) ) == relation and isinstance(v,SuperDoc):
            r = getattr(self.__class__, k)
            fkey = getattr( v, r._pk[0] )
            setattr( self.__dict__['_data'], r._pk[1], type(fkey) == ObjectId and str(fkey) or fkey )
        else:
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
        # fitur cascade tidak support many-to-many relation
        self._call_relation_attr('_delete_cascade')
        
        # update relation list metadata
        rels = filter( lambda x: type( getattr( self.__class__, x ) ) == relation, dir(self.__class__) )
        for rel in rels:
            
            vrela = getattr( self.__class__, rel )
            
            if vrela._type != 'many-to-many':
               break
            
            keyrel = getattr( vrela, '_keyrel' )
            
            if not hasattr(self, keyrel[0]):
                break
            
            backref = getattr( vrela, '_backref' )
            
            rela = getattr( vrela, '_get_rel_class' )()
            mykey = getattr(self.__dict__['_data'],backref[1])
            
            all_rela_obj = self._db[rela._collection_name].find({ keyrel[0]: mykey })
            
            col_save = self._db[rela._collection_name].save
            
            for rela_obj in all_rela_obj:
                
                rela_obj[keyrel[0]].remove(mykey)
                col_save(rela_obj)
                
        
        Doc.delete(self)
    

    def __repr__(self):
        
        if self._saved():
            return '<SuperDoc(id=%s)>' % self.__dict__['_data']._id
        else:
            return '<SuperDoc(id=Unsaved)>'





