import logging

from antypes import *
from exc import RelationError
from doclist import DocList, SuperDocList
from pymongo import ASCENDING, DESCENDING
from pymongo.objectid import ObjectId
from const import relation_reserved_words
from utils import parse_query
from pendingop import PendingOperation

import random, copy

global mapped_user_class_docs
mapped_user_class_docs = {}
MAX_RECURSION_DEEP = 10
RELATION_RECURSION_DEEP = 0

log = logging.getLogger(__name__)

class relation(object):
    
    def __init__(self,rel_class=None,**kwargs):
        
        
        self._internal_params = kwargs
        
        self.__dict__['_data'] = kwargs.get('listmode') and [] or None
            
        self._old_hash = -1
        self._current_hash = 0
        self._rel_class_name = rel_class
        
        self._type = kwargs.get('type')
        
        
        if self._type is None:
            self.listmode = kwargs.get('listmode')
            if self.listmode is None:
                self._type = 'one-to-many'
                self.listmode = True
            else:
                self._type = self.listmode == True and 'one-to-many' or 'one-to-one'
        else:
            self.listmode = self._type not in ('one-to-one','many-to-one')

        if self._type == 'many-to-many':
            
            # setup for many-to-many relational type requirements
            
            self._keyrel = kwargs.get('keyrel')
            
            if not self._keyrel:
                raise RelationError, "many-to-many relation need a keyname"
            
            self._backref = kwargs.get('backref')
            
            if not self._backref:
                raise RelationError, "many-to-many relation need a backref"
            
            self._backref = self._backref.split(':')
            self._keyrel = self._keyrel.split(':')
            
        elif self._type in ('one-to-many','one-to-one'):
            
            self._backref = kwargs.get('backref')
            
            # no many-to-many, need PK-FK
        
            rv = kwargs.get('pk')
            if not rv:
                raise RelationError, "Bad relation. No PK defined"
            
            self._pk = rv.split('==')
            
            cond = kwargs.get('cond')
            if cond:
                self._cond = isinstance(cond, ConditionQuery) and cond or and_(cond)
            else:
                # use pk
                self._cond = and_(**{self._pk[0]:':%s' % self._pk[1]})
                
        elif self._type == 'many-to-one':
            
            rv = kwargs.get('pk')
            if not rv:
                raise RelationError, "many-to-one relation need pk"
            
            self._pk = rv
            self._cond = and_( _id = ':%s' % rv )
            
            
                
                
        if self._type != 'one-to-one':
            self._order = kwargs.get('order')
        
        self._cascade = kwargs.get('cascade', None)
        self._parent_class = None
        
        self.__dict__['_deleted_item'] = []
        self.__dict__['_cached_repr'] = []
        self.__dict__['_new_data'] = []
        
        # execution stack after saving operation
        self._post_save = PendingOperation(self)
        
    def copy(self):
        '''Create new copy of me
        '''
        return relation(self._rel_class_name, **self._internal_params)

    def __repr__(self):
        self.refresh()
        if self.listmode:
            item_count = self.__dict__['_data'] is not None and self.__dict__['_data'].count() or 0
            if item_count>10:
                return "%s ...(and %d more)..." % ( str( self.__dict__['_cached_repr'][:10] ), item_count - 10 )
            return repr( self.__dict__['_cached_repr'] )
        return repr( self.__dict__['_data'] )
        
    @property
    def changed(self):
        return self._current_hash != self._old_hash or len(self.__dict__['_new_data']) > 0 or len(self.__dict__['_deleted_item']) > 0

    def _update_hash(self):
        self._current_hash = str(abs(hash(random.random())))
        
    def _update_index( self, key, ttl=6000 ):
        '''Untuk meng-index db, kalo diperlukan.
        '''
        #@TODO: lanjutkan!
        self._parent_class._monga._db[self._parent_class._collection_name].ensure_index(key,ttl=ttl)

    def refresh(self):

        if self.changed is True:
            #print 'data changed, (re)populate list...'
            self.reload()
            
        if self.listmode:
            if type(self.__dict__['_data']) == SuperDocList :
                self.__dict__['_data'].tofirst()

    def count(self):
        
        self.refresh()
        
        if self.listmode:
            return self.__dict__['_data'].count()
        return None
        
        
    def __get_where_clause(self):
        
        if self._type == 'many-to-many':
            
            d = getattr(self._parent_class.__dict__['_data'], self._keyrel[0])
            
            if d is None:
                return d
            
            rv = { self._keyrel[1] : {'$in' : d } }

        else:
            rv = self._cond.where( **dict(map( lambda x: (x, hasattr(self._parent_class.__dict__['_data'], x.startswith(':') and x[1:] or x) and getattr(self._parent_class.__dict__['_data'], x.startswith(':') and x[1:] or x) or None ), self._cond.raw.values() )))
        
        if rv and type(rv) == dict:
            
            if self._parent_class._monga.config.get('nometaname') == False and self._type != 'many-to-one':
                
                # uses metaname
                
                def get_siblings():
                    global mapped_user_class_docs
                    
                    rc = self._get_rel_class()
                    siblings = [rc.__name__]
                    
                    for k,sb in mapped_user_class_docs.iteritems():
                        parent = sb.__bases__[0]
                        while(True):
                            if parent.__name__ == "SuperDoc": break
                            if parent.__name__ == rc.__name__:
                                siblings.append( sb.__name__ )
                                break
                            parent = parent.__bases__[0]
                            
                    return siblings
                
                #from dbgp.client import brk; brk()
                rv['_metaname_'] = {'$in' : get_siblings()}
            
        return rv
        

    def reload(self):
        '''Load data dari db.
        the rule is... masupin dulu ke cache, cache dialokasikan sebesar
        jumlah item di dalamnya dan di-null-kan, tetapi baru di isi dengan max 10 item dulu,
        yg lainnya nyusul bergantung permintaan dari user.
        '''
        
        if not self.__ready_db_read(): return None
        
        if self._parent_class._saved() == False: return None
            
        self._old_hash = self._current_hash
 
        _cond = self.__get_where_clause()
        
        if self._parent_class._echo == True:
            print 'query: %s' % repr(_cond)
        
        if not _cond: return None 
        
        rel_class = self._get_rel_class()

        if self.listmode:
            
            rv = SuperDocList (
                DocList( self._parent_class._monga,
                        rel_class,
                        self._parent_class._monga._db[rel_class._collection_name].find( _cond )
                        )
                )
            
            # alokasikan null memory sebesar jumlah item pada db
            if self._order is not None:
                cached_data = rv.sort( **self._order ).limit(10).all() # maximum to 10...
            else:
                cached_data = rv.sort(_id=1).limit(10).all() # maximum to 10...
                
            if rv.count() > 10:
                cached_data += [ None for x in xrange(0,rv.count() - 10) ]
            
            self.__dict__['_cached_repr'] = cached_data

            self.__dict__['_data'] = SuperDocList (
                DocList( self._parent_class._monga,
                        rel_class,
                        self._parent_class._monga._db[rel_class._collection_name].find( _cond )
                        )
                )
            
            return self.__dict__['_data']
            
        # single mode one-to-one type
        rv = self._parent_class._monga._db[rel_class._collection_name].find_one( _cond )
        self.__dict__['_data'] = rv and rel_class( self._parent_class._monga, **dictarg(rv) ) or None
            
        return self.__dict__['_data']
        
        
    def __ready_db_read(self):
        return hasattr( self, '_parent_class' ) and self._parent_class is not None
        
        
    def find( self, **kwargs ):
        '''Untuk mencari item berdasarkan kunci :kwargs,
        hanya untuk relasi jenis one-to-many dan many-to-many.
        '''
        if self._type is 'one-to-one':
            raise RelationError, "this function only for one-to-many and or many-to-many relation"
        
        if not self.__ready_db_read(): return None
        
        _cond = self.__get_where_clause()
        
        if not _cond: return None
        
        addf = kwargs
        if '_id' in kwargs:
            addf['_id'] = ObjectId(str(kwargs['_id']))
            
        _cond.update( parse_query( addf ) )
        
        if self._parent_class._echo == True:
            print 'query: %s' % repr(_cond)
        
        rel_class = self._get_rel_class()
        
        rv = self._parent_class._monga._db[rel_class._collection_name].find_one( _cond )
        return rv and rel_class( self._parent_class._monga, **dictarg(rv) ) or None
        
        
    def filter( self, **kwargs ):
        '''Filter item berdasarkan kunci :kwargs.
        hanya untuk relasi jenis one-to-many dan many-to-many.
        return:
            SuperDocList
        '''
        if self._type is 'one-to-one':
            raise RelationError, "this function only for one-to-many and or many-to-many relation"
        
        if not self.__ready_db_read(): return None
        
        _cond = self.__get_where_clause()
        
        if not _cond: return None
        
        if len(kwargs) > 0:
            _cond.update( parse_query( kwargs ) )
        
        if self._parent_class._echo == True:
            print 'query: %s' % repr(_cond)
        
        rel_class = self._get_rel_class()
        
        return SuperDocList (
            DocList( self._parent_class._monga,
                    rel_class,
                    self._parent_class._monga._db[rel_class._collection_name].find( _cond ).sort('_id',ASCENDING)
                    )
            )
        
    def query(self, **kwargs):
        '''Get objects for quick delete or update.
        Example:
            user.messages.query(_id__in = [1,2,3]).delete()
        '''
        
        if self._type is 'one-to-one':
            raise RelationError, "this function only for one-to-many and or many-to-many relation"
        
        if not self.__ready_db_read(): return None
        
        _cond = self.__get_where_clause()
        
        if not _cond: return None
        
        if len(kwargs) > 0:
            _cond.update( parse_query( kwargs ) )
        
        if self._parent_class._echo == True:
            print 'query: %s' % repr(_cond)
        
        rel_class = self._get_rel_class()
        
        return self._parent_class._monga.col(rel_class).query(**kwargs)
        
    
    def all(self):
        '''Mendapatkan semua record pada relasi.
        hanya untuk relasi jenis one-to-many dan many-to-many.
        return:
            SuperDocList
        '''
        return self.filter().all()
        
    def _get_rel_class(self):
        global mapped_user_class_docs
        if not hasattr(self, 'rel_class'):
            if self._type == 'many-to-one':
                self._rel_class_name = str(getattr(self._parent_class.__dict__['_data'], '__meta_pcname__'))
            
            try:
                self.rel_class = type(self._rel_class_name) == str and mapped_user_class_docs[self._rel_class_name] or self._rel_class_name
            except KeyError:
                raise RelationError, "Resource class `%s` not mapped. try to mapper first." % self._rel_class_name
        return self.rel_class

        
    def explain(self):
        return RelationDataType(self)


    def _is_data_related(self, data):
        rv = data.__class__.__name__ == self._rel_class_name or \
            self._rel_class_name in [ x.__name__ for x in data.__class__.__bases__ ] # periksa juga untuk super-class-nya
        return rv
        

    def append(self, data):

        # just for one-to-many or many-to-many relation
        if self.listmode is False:
            raise RelationError, "non one-to-many or many-to-many relation"

        if not self._is_data_related(data):
            raise RelationError, "data not related: %s <=> %s" % (self._rel_class_name,type(data))
            
        if self._type in ('one-to-many','one-to-one') and self._pk[1] != '_id' and not self._parent_class.__dict__['_data']._hasattr(self._pk[1]):
            raise RelationError, "%s has no attribute %s" % (self._parent_class.__class__.__name__, self._pk[1])
            
        # untuk data child berupa relasi many-to-one
        if self._type == 'one-to-many' and self._backref is not None:
            
            t = getattr( data, self._backref )
            
            if t is not None:
                if t._type == 'many-to-one':
                    
                    # tambahkan record tambahan buat meta parent class name
                    # berfungsi untuk parent class lookup di relasi model many-to-one
                    data.__meta_pcname__ = self._parent_class.__class__.__name__
            
        data.set_monga( self._parent_class._monga )
        
        self.__dict__['_new_data'].append(data)
        self.__dict__['_cached_repr'].append(data)
        
        self.__child_modif(item=data,diff='add-new')
        
    
    def remove(self, data):
        
        x = getattr( self._parent_class.__dict__['_data'], self._keyrel[0] )
        if data._id in x:
            self.__dict__['_cached_repr'] = filter( lambda x: x._id != data._id, self.__dict__['_cached_repr']) 
            x.remove( data._id )
            return setattr( self._parent_class.__dict__['_data'], self._keyrel[0], x )
        return False
    
    
    def clear(self):
        '''untuk menghapus semua item yang terelasi.
        hanya berlaku untuk realsi tipe one-to-many aja.
        '''
        
        if self._type != 'one-to-many':
            raise RelationError,"this method only for one-to-many relation type"
        
        rv = self._parent_class._monga._db[self.rel_class._collection_name].remove({})
        
        self._update_hash()
        
        return rv


    def _save(self):

        if self.listmode:
            
            _datas = [ x for x in self.__dict__['_new_data'] if x is not None ]
            _datas.extend([ x for x in self.__dict__['_cached_repr'] if x is not None and x not in _datas])

            for data in _datas:
                
                #   
                # build relation metadata
                #
                
                if self._type == 'one-to-many':
                    
                    if not data._changed() and getattr(data,self._pk[0]) is not None: continue
                    
                    if hasattr( self._parent_class.__dict__['_data'], self._pk[1] ):
                        
                        new_attr = getattr(self._parent_class.__dict__['_data'], self._pk[1])
                        new_attr = type(new_attr) in [int,long] and new_attr or type(new_attr) == ObjectId and new_attr.binary.encode('hex') or new_attr is not None and str(repr(new_attr)) or new_attr
                
                        data.__setattr__(self._pk[0],new_attr)
                    else:
                        raise RelationError, "Cannot build relation metadata invalid pk"
                    
                    rels = filter( lambda x: type( getattr(data.__class__, x) ) == relation, dir(data.__class__) )
                    
                    
                    for rel in rels:
                        
                        if not hasattr(data.__dict__['_data'], rel):
                            continue
                        
                        rawd = getattr(data.__dict__['_data'], rel)
                        
                        if rawd is None:
                            continue
                        
                        if type( rawd ) == RelationDataType:
                            continue
                        
                        r = getattr(data.__class__, rel)
                        v = getattr( rawd , r._pk[0] )
                        v = type(v) == ObjectId and v.binary.encode('hex') or v
                        
                        setattr( data.__dict__['_data'], r._pk[1], v )
                        
                        # delete it after used
                        delattr( data.__dict__['_data'], rel )
                        
                    if data._monga is None:
                        data.set_monga(self._parent_class._monga)
                        
                    data.save()
                    del self.__dict__['_new_data'][:]
                    
                elif self._type == 'many-to-many':
                    
                    if not self._parent_class.__dict__['_data']._hasattr(self._keyrel[0]):
                        setattr( self._parent_class.__dict__['_data'], self._keyrel[0], [] )
                    
                    rc = self._get_rel_class()
                    
                    if not data.__dict__['_data']._hasattr(self._keyrel[1]):
                        raise RelationError, "many-to-many relation `%s` empty keyrel for `%s`" % (data.__class__.__name__,self._keyrel[1])
                    
                    key = getattr( data.__dict__['_data'], self._keyrel[1] )
                    
                    # check if key already exists, prevent multiple reinsertion metadata
                    if key not in getattr( self._parent_class.__dict__['_data'], self._keyrel[0] ):
                        getattr( self._parent_class.__dict__['_data'], self._keyrel[0] ).append( key  )
                    
                    if not data.__dict__['_data']._hasattr( self._backref[0] ):
                        setattr( data.__dict__['_data'], self._backref[0], [] )
                     
                    key = getattr( self._parent_class.__dict__['_data'], self._backref[1] )
                    
                    # check if key already exists, prevent multiple reinsertion metadata
                    if key not in getattr( data.__dict__['_data'], self._backref[0] ):
                        getattr( data.__dict__['_data'], self._backref[0] ).append( key )
                    
                    # update child relation
                    data.__dict__['_data']._id = \
                        self._parent_class._monga._db[data._collection_name].save(data.to_dict())
                    
                elif self._type == 'many-to-one':
                    
                    #tambah meta name buat lookup parent relation class
                    data.__dict__['_data'].__meta_pcname__ = pcname
                    
                    data.__dict__['_data']._id = \
                        self._parent_class._monga._db[self._parent_class._collection_name].save(data.to_dict())
                    
                    
            if self._type == 'many-to-many':
                # save/update parent class
                self._parent_class.__dict__['_data']._id = self._parent_class._monga._db[self._parent_class._collection_name].save(self._parent_class.to_dict())
                
            del self.__dict__['_new_data'][:]
            
        else:
            # one-to-one
            
            #self._post_save.apply_op_all()
            
            if self.__dict__['_data']:
                self.__dict__['_data'].save()
        
        
        # delete pending data
        
        if len(self.__dict__['_deleted_item']) > 0:
            for data in self.__dict__['_deleted_item']:                
                data.delete()
                
            del self.__dict__['_deleted_item'][:]
            
            
    def _delete_cascade(self):
        '''Ngapus kabeh isi child neng sak jeroning relasi
        '''
        
        if not self.listmode: 
            #raise RelationError, "cascade action only support for listmode relation"
            return False
        
        if self._cascade != 'delete':
            #raise RelationError, "not implemented with cascade support"
            return False
        
        if self._type == 'many-to-many':
            raise RelationError, "Many-to-many relation not support cascade"
            
        self.reload()
        _datas = self.__dict__['_data']
        
        if _datas is not None:
            for data in _datas:
                data.delete()
            
        del self.__dict__['_cached_repr'][:]
        return True
            

    def __getitem__(self, k):
        '''Mendapatkan item secara subscript,
        diambil dari cache dulu, kalo gak ada baru ambil dari db
        '''
        self.refresh()
        
        if self.listmode:
            if len(self.__dict__)>0:
                
                # convert k if -1 (pythonic method for get last item inside of list)
                k = k == -1 and (self.__dict__['_data'].count() - 1) or k
                
                if len(self.__dict__['_cached_repr']) > k and self.__dict__['_cached_repr'][k] is not None:
                    return self.__dict__['_cached_repr'][k]
                    
                elif len(self.__dict__['_new_data']) > k:
                    return self.__dict__['_new_data'][k]
                    
                if self._order is not None:
                    rv = self.__dict__['_data'].sort( **self._order ).skip(k).limit(1).first()
                else:
                    rv = self.__dict__['_data'].sort( _id = 1 ).skip(k).limit(1).first()
                if rv is not None:
                    # simpan di cache pada point ke k
                    self.__dict__['_cached_repr'][k] = rv
                    return rv
                raise IndexError, "Index out of range"
            else:
                raise RelationError, "No data with key %s" % k
        return self.__dict__['_data']
        
        
    def __len__(self):
        self.refresh()
        if self.__dict__['_cached_repr']:
            return len(self.__dict__['_cached_repr'])
        return 0
        
    def __nonzero__(self):
        self.refresh()
        return (self.__dict__['_cached_repr'] or self.__dict__['_data']) is not None
        
    def __getattr__(self, key):
        
        if key in relation_reserved_words:
            return object.__getattribute__(self, key)
        
        self.refresh()
        
        if not hasattr( self.__dict__['_data'], key ):
            return None
        
        return getattr( self.__dict__['_data'], key  )
        
    def __cmp__(self,other):
        if self._type == 'one-to-one':
            if other is None: return -1
            return cmp(self._id,other._id)
        return -1
        
    def __setattr__(self, key, value):
        
        if key in relation_reserved_words:
            return object.__setattr__( self, key, value )
        
        if self._type != 'one-to-one':
            return object.__setattr__( self, key, value )
            #raise AttributeError, "%s instance has no attribute '%s'" % (self.__class__.__name__, key)
        
        self.refresh()
        
        setattr( self.__dict__['_data'], key, value )
        
        #self._post_save.add_op(self.__dict__['_data'], action='setattr', key=key, value=value )
        
        
    def __delitem__(self, k):
        
        #k = k == -1 and (self.__dict__['_data'].count() - 1) or k
        
        if type(k) == slice:
            self.__dict__['_deleted_item'].extend(self[k])
        else:
            self.__dict__['_deleted_item'].append(self[k])
        
        self.__child_modif(item=self.__dict__['_cached_repr'][k],diff='deleted')
        
        del self.__dict__['_cached_repr'][k]

        
    def __child_modif(self, **info):
        '''Nggo nandai nek terjadi modifikasi nang anakane
        '''
        self._parent_class.__dict__['_modified_childs'].append(info)
        

class this(object):
    
    def __init__(self,at):
        self.at = at
        
    def __repr__(self):
        return str(self.at)
    

class query(object):
    
    def __init__(self,rel_class_name,filter_={}):
        self._rel_class_name = rel_class_name
        self.rel_class = None
        self.filter = filter_
        self._parent_class = None
        
        
    def _get_rel_class(self):
        global mapped_user_class_docs
        if self.rel_class == None:
            try:
                self.rel_class = type(self._rel_class_name) == str and mapped_user_class_docs[self._rel_class_name] or self._rel_class_name
            except KeyError:
                raise RelationError, "Resource class `%s` not mapped. try to mapper first." % self._rel_class_name
        return self.rel_class
    
    def _get_cond(self):
        _cond = {}
        
        for k, v in self.filter.iteritems():
            if type(v) == this:
                at = getattr(self._parent_class,str(v))
                if at != None:
                    _cond[k] = type(at) == ObjectId and unicode(at) or at
            else:
                _cond[k] = v
                
        return parse_query(_cond)
        
    def __call__(self):

        _cond = self._get_cond()
        rel_class = self._get_rel_class()
        
        return SuperDocList (
            DocList(
                self._parent_class._monga,
                rel_class,
                self._parent_class._monga._db[rel_class._collection_name].find( _cond )
            )
        )
        
    def find(self,**cond):
        _cond = self._get_cond()
        _cond.update(cond)
        
        rel_class = self._get_rel_class()
        return self._parent_class._monga.col(rel_class).find( **cond )
        
    def __iter__(self):
        
        _cond = self._get_cond()
        rel_class = self._get_rel_class()
        
        return SuperDocList (
            DocList(
                self._parent_class._monga,
                rel_class,
                self._parent_class._monga._db[rel_class._collection_name].find( _cond )
            )
        ).__iter__()
        
    def __getattr__(self,key):
        
        if key in ("filter","find"): return object.__getattr__(self,key)
        
        _cond = self._get_cond()
        rel_class = self._get_rel_class()
        
        sdl = SuperDocList (
            DocList(
                self._parent_class._monga,
                rel_class,
                self._parent_class._monga._db[rel_class._collection_name].find( _cond )
            )
        )
        return getattr(sdl,key)
        
    def __repr__(self):
        return "<Dynamic Query Load [%s]>" % self._rel_class_name


class RelationDataType(object):
    
    def __init__(self, val):
        self.val = val
        
    def __repr__(self):
        t = self.val._type
        if t in ('one-to-many','one-to-one'):
            return "<relation to [%s pk(%s==%s)]>" % (self.val._rel_class_name,self.val._pk[0],self.val._pk[1])
        elif t == 'many-to-one':
            return "<relation to [many-to-one]>"
        else:
            return "<relation to [many-to-many: %s]>" % self.val._rel_class_name
    

def mapper(*objs):
    
    global mapped_user_class_docs
    
    mapped_user_class_docs.update( dict(map(lambda x: (x.__name__, x), objs )) )
    
def clear_mapper():
    global mapped_user_class_docs
    mapped_user_class_docs.clear()

