#@TODO: finish this code
from doc import Doc
from pymongo.dbref import DBRef
from pymongo.objectid import ObjectId
from nested import Nested
from antypes import *
from exc import *
from orm import *
from const import *
from pendingop import PendingOperation
import connector

import types


class SuperDoc(Doc):
    '''Advanced document for mongo ORM data model
    '''
    
    def __init__(self, _monga_instance=None, **datas):
        
        # build reserved entry name
        self.__dict__['_reserved_entry_name'] = []
        
        rel_names = filter( lambda x: type( getattr(self.__class__, x) ) == relation, dir(self.__class__) )

        for reln in rel_names:
            rel = getattr( self, reln )
            if rel._type == 'many-to-many':
                self.__dict__['_reserved_entry_name'].append(rel._keyrel[0])
            else:
                self.__dict__['_reserved_entry_name'].append(reln)
        
        self._pending_ops = PendingOperation(self)
        
        _monga_instance = _monga_instance or connector.db_instance
        
        self._load( _monga_instance, **datas )
        self._echo = False
        
    def _load(self, _monga_instance, **datas):
        
        self._monga = _monga_instance
        
        self.__dict__['_data'] = Nested(datas)
        
        _has_opt = hasattr( self, '_opt' )
        
        if _has_opt:
            if self._opt.get('strict') == True:
                for k in datas.keys():
                    if not self.__has_entryname(k):
                        raise SuperDocError, "`%s` is strict model. Cannot assign entryname for `%s`" % ( self.__class__.__name__,k )

        self.__sanitize()
        self.__assign_attirbutes( datas )
        
        
        if _has_opt:
            
            cls_bases = self.__class__.__bases__
        
            # invokes multiple inheritance _opt
            
            for i,cl in enumerate(cls_bases):
                if i > 0 and not hasattr(cl, "_opt"):
                    continue
                if i > 0:
                    _opt = getattr(cl,"_opt")
                else:
                    _opt = getattr(self,"_opt")
                    
                if not self._saved() and _opt.has_key('default'):
                    for k, v in _opt['default'].iteritems():
                        if hasattr(self, k):
                            if getattr(self.__dict__['_data'], k) is None:
                                if type( v ) in [types.FunctionType, types.BuiltinFunctionType]:
                                    setattr( self.__dict__['_data'], k, apply( v ) )
                                else:
                                    setattr( self.__dict__['_data'], k, v )
                        else:
                            raise SuperDocError, \
                                '`%s` has no entryname `%s` for default value assignment' \
                                % (self.__class__.__name__,k)

        #@TODO: mungkin butuh optimasi?
        for x in filter( lambda y: y!="__class__", dir(self.__class__)):
            
            o = getattr( self.__class__, x )
            ot = type( o )
            
            if ot == property or ot not in (relation, query, types.TypeType, dict):
                continue
            
            if getattr( self, x ) == None:
                continue
            
            if ot == relation:
            
                _t = getattr(self,x)
                
                if type(_t) == types.NoneType:
                    continue
                
                if _t._type == 'one-to-one' and self._monga is not None:
                    
                    # lookup for existance relation in db
                    # if not exists, then None it!
                    rv = None
                    try:
                        rv = getattr(self,_t._pk[1])
                    except:
                        pass
                    
                    if rv is not None:
                        rv = _t._pk[0] == '_id' and ObjectId(str(rv)) or type(rv) is ObjectId and str(rv) or rv
                        rv = self._monga._db[_t._get_rel_class()._collection_name].find({_t._pk[0]: rv}).count()
                        
                    if rv is None or rv == 0:
                        setattr( self, x, None )
                        setattr( self.__dict__['_data'], x, None )
                        continue
                
                _t = _t.copy()
                _t._parent_class = self
                
                setattr(self,x,_t)
                
                if _t._type == 'many-to-many':
                    if not self._hasattr( _t._keyrel[0] ):
                        setattr( self, _t._keyrel[0], [] ) # reset m2m relation meta list
            
            elif ot == query:
                
                _t = getattr(self,x)
                
                if type(_t) == types.NoneType:
                    continue
                
                _t._parent_class = self
                
                setattr(self,x,_t)
            
            elif ot == types.TypeType:
                
                # khusus buat inisialisasi empty list, default is []
                sx = x.startswith('_x_') and x[3:] or x
                
                sot = type( getattr( self, sx ) )
                
                if o == list and sot != list:
                    setattr( self.__dict__['_data'], sx, [] )
                    
                elif o == dict and sot != Nested:
                    setattr( self.__dict__['_data'], sx, Nested() )

        self.__dict__['_modified_childs'] = []
        
        
    def __assign_attirbutes(self, datas):
        for k, v in datas.iteritems():
            
            # except bad options types
            try:
                ov = getattr(self.__class__, k)
            except:
                ov = None
            if ov and type(ov) is options:
                if v not in ov:
                    raise SuperDocError, "`%s` cannot assign entryname for `%s = %s` invalid options, can only: `%s`" % (
                        self.__class__.__name__,
                        k,
                        v,
                        str(', '.join([str(x) for x in ov]))
                    )
            
            self.__setattr__( k, v )
            
        
    def set_monga(self, _monga):
        self._monga = _monga

    def __sanitize(self):
        
        # map class atribute based user definition to _data container collection
        _attrs = filter( lambda x: type(getattr(self.__class__,x)) in (types.TypeType, options) and x not in ['__class__'], dir(self.__class__) )

        #from dbgp.client import brk; brk()
        #if str(self.__class__.__name__) == 'User':
        #    pass

        for x in _attrs:

            y = x
            if type(getattr(self,x)) != relation:
                
                if not x.startswith('_x_'):
                    
                    v = getattr(self.__class__, x)
                    setattr(self.__class__, '_x_%s' % x, v )
                    
                    try:
                        delattr(self.__class__, x)
                    except AttributeError:
                        #from dbgp.client import brk; brk()
                        # kalo error coba deh hapus dari super-class-nya kalo ada tapi...
                        for cl in self.__class__.__mro__[1:-3]:
                            
                            # pasang attribut di tiap class yang diturunkan
                            setattr(cl, '_x_%s' % x, v)
                            
                            try:
                                delattr(cl, x)
                            except:
                                pass

                else:

                    y = x[3:]
            
            if getattr( self.__dict__['_data'], y ) is None:
                # re-set it with None again!
                setattr( self.__dict__['_data'], y, None )
            
    def validate(self):
        
        if not hasattr( self, '_opt' ):
            return 'not checked'
        
        req = self._opt.get('req')
        if req is not None:
            for x in req:
                
                if getattr( self, x ):
                    if getattr(self,x) is None:
                        raise SuperDocError, "%s require value for %s" % (self.__class__.__name__,x)
                else:
                    raise SuperDocError, "%s has no required value for %s" % (self.__class__.__name__,x)

        return 'OK'

    def save(self):
        '''Save/insert doc
        @TODO: buat acknowledge biar tau save/insert-nya berhasil atau gak?
        '''

        self.validate()
        
        if self._monga is None:
            raise SuperDocError, "This res not binded to monga object. Try to bind it first use set_monga(<monga instance>)"
        
        if self._monga.config.get('nometaname') == False:
            # buat metaname untuk modelnya
            
            setattr( self.__dict__['_data'], '_metaname_', self.__class__.__name__ )
        
        # reset dulu error tracknya, buat jaga kalo2 dibutuhkan buat error checking
        self._monga._db.reset_error_history()

        Doc.save(self)
        
        if self.get_last_error() is not None:
            return None
        
        global RELATION_RECURSION_DEEP, MAX_RECURSION_DEEP
        
        RELATION_RECURSION_DEEP += 1
        
        if RELATION_RECURSION_DEEP < MAX_RECURSION_DEEP:
            
            self._call_relation_attr( '_update_hash' )
            self._call_relation_attr( '_save' )
            
            RELATION_RECURSION_DEEP -= 1
        else:
            raise SuperDocError, "Recursion limit reached, max %d" % MAX_RECURSION_DEEP
        
        # eksekusi pending ops
        if not self._pending_ops.empty():
            self._pending_ops.apply_op_all()
        
        # refresh relation state
        self.__map_relation()
        
        return self
        
    
    def get_last_error(self):
        '''Kanggo ngolehake informasi errore.
        nek raono error yo None lah return-ne.
        '''
        return self._monga._db.previous_error()


    def _call_relation_attr(self, attr, *args, **kwargs):

        for x in filter( lambda x: type(getattr(self.__class__,x)) == relation, dir(self.__class__) ):
            
            t = getattr( self, x )
            
            if t is None: continue
            
            # jangan save many-to-one relation
            if t._type == 'many-to-one':
                continue
            
            if hasattr(t, attr):
            
                getattr(t,attr)( *args, **kwargs )
                
                
    def refresh(self):
        '''Reload data from database, for keep data up-to-date
        '''
        
        if self._id is None:
            raise SuperDocError, "Cannot refresh data from db, may unsaved document?"
        
        doc = self._monga._db[self._collection_name].find_one(self._id)
        
        if not doc:
            return False
        
        self._load( self._monga, **dictarg(doc) )
        self.__map_relation()
        
        return True
    
    
    def __map_relation(self):
        '''Untuk menge-map relasi dengan cara me-reload semua relasinya
        agar up-to-date dengan db.
        '''
        for x in filter( lambda x: type( getattr(self.__class__,x) ) == relation , dir(self.__class__) ):
            
            rel = getattr( self, x )
            if rel is not None and rel._type != 'many-to-one':
                rv = rel.reload()
                if rel._type == 'one-to-one':
                    if type(rv) == types.NoneType:
                        setattr ( self, x, None ) # null it

            else:
                # reload relation
                rel = getattr( self.__class__, x ).copy()
                rel._parent_class = self
                
                if rel._type != 'many-to-one':
                    rv = rel.reload()
                    if rv is not None:
                        setattr( self, x, rel )
                    else:
                        setattr( self, x, None ) # null it

    
    def __cmp__(self, other):
        if other is None:
            return -1
        if self.__dict__['_data']._id is None or other.__dict__['_data']._id is None:
            return -1
        return cmp( self._id, other._id)


    def __getitem__(self, k):
        return getattr(self.__dict__['_data'], k)
        
    
    def __getattr__(self, k):
        
        if k in ('_opt','__methods__', '_hasattr'):
            return Doc.__getattr__(self, k)
            
        v = getattr(self.__dict__['_data'], k)
        
        if v != None:
            
            if ( type( v ) == relation ):
                return getattr( v, k )
        
        if not k.startswith('__') and k in dir(self.__dict__['_data']):
            return v
            
        return Doc.__getattr__(self, k)
    
    
    def __has_entryname(self, name):
        if name in superdoc_reserved_words: return True
        
        # periksa apakah meta name, terutama pada relation many-to-many
        # kembalikan True apabila berupa meta name khusus
        if name in self.__dict__['_reserved_entry_name']: return True
        
        return (hasattr(self.__class__, name) and \
                type(getattr(self.__class__, name)) in [relation, types.TypeType, options]) or \
                hasattr(self.__class__, '_x_%s' % name)
        
        
    def __setattr__(self, k, v):
        
        # check is keyname not in restrict_attribute_names
        if k in restrict_attribute_names:
            raise SuperDocError, "`%s` have restricted keyword `%s`. Please put another name." % (self.__class__.__name__,k)
        
        if k in superdoc_reserved_words or k.startswith('_x_'):
            return Doc.__setattr__(self, k , v)
        
        if self.__dict__.has_key('_opt') and self._opt.get('strict') == True:
            if self.__has_entryname( k ) == False:
                raise SuperDocError, "`%s` is strict model. Cannot assign entryname for `%s`" % ( self.__class__.__name__,k )
        
        if hasattr( self.__class__, '_x_%s' % k ):
            typedata = getattr( self.__class__, '_x_%s' % k )
            #v = type(v)==str and unicode(v) or v
            if typedata != type(v) and type(v) is not types.NoneType:
                
                if typedata is bool and v not in (1,0):
                    raise SuperDocError, "mismatch data type `%s`=%s and `%s`=%s" % (k,typedata,v,type(v))
                    
                # try to convert it if possible
                try:
                    v = typedata(v)
                except:
                    raise SuperDocError, "mismatch data type `%s`=%s and `%s`=%s" % (k,typedata,v,type(v))
            
        # check if one-to-one relation
        # just map it to pk==fk
        if hasattr(self.__class__,k) and type( getattr(self.__class__,k) ) == relation and isinstance(v,(SuperDoc,relation)):
            
            if type(v) == relation:
                Doc.__setattr__(self, k , v)
                if v._type != 'one-to-one' or v._data is None:
                    return
            
            r = getattr(self.__class__, k)
            
            if r._pk[0] == '_id':
                if not hasattr(v,'_id') or v._id == None:
                    if self._monga is None:
                        raise RelationError, "cannot auto-save one-to-one relation in smart object assignment. is object not binded with monga instance?"
                    # may unsaved doc, save it first
                    v.set_monga(self._monga)
                    v.save()
                    
            elif not v._hasattr(r._pk[0]):
                raise RelationError, "relation model `%s` don't have keyname `%s`" % (v.__class__.__name__, r._pk[0])
            
            fkey = getattr( v, r._pk[0] )
            if fkey is not None:
                setattr( self.__dict__['_data'], r._pk[1], type(fkey) == ObjectId and str(fkey) or fkey )
            else:
                # relasi terbalik berarti masukin ke pending ops ajah...
                fkey = getattr( self.__dict__['_data'], r._pk[1] )
                self._pending_ops.add_op( v, 'setattr', key=r._pk[0], value=ObjectId and str(fkey) or fkey )
                self._pending_ops.add_op( v, 'save' )
                
        else:
            Doc.__setattr__(self, k , v)


    def __delitem__(self, k):
        print 'test'
        delattr(self.__dict__['_data'], k)

    
    def _saved(self):
        return getattr(self.__dict__['_data'],'_id') is not None
        
    
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
            
            if getattr(self, keyrel[0]) is None:
                break
            
            backref = getattr( vrela, '_backref' )
            
            rela = getattr( vrela, '_get_rel_class' )()
            mykey = getattr(self.__dict__['_data'],backref[1])
            
            all_rela_obj = self._monga._db[rela._collection_name].find({ keyrel[0]: mykey })
            
            col_save = self._monga._db[rela._collection_name].save
            
            for rela_obj in all_rela_obj:
                
                rela_obj[keyrel[0]].remove(mykey)
                col_save(rela_obj)
                
        
        return Doc.delete(self)
    
    # support pickle protocol
    def __getstate__(self):
        return self.__dict__['_data']
    
    # support pickle protocol    
    def __setstate__(self,d):
        self.__dict__['_data'] = d

    def __repr__(self):
        
        if self._saved():
            return '<SuperDoc(id=%s)>' % self.__dict__['_data']._id
        else:
            return '<SuperDoc(id=Unsaved)>'





