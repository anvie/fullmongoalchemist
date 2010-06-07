from pymongo.dbref import DBRef
from pymongo.objectid import ObjectId
from pymongo.code import Code
from superdoc import SuperDoc
from doclist import DocList, SuperDocList
from exc import SuperDocError

import types

# patch DBRef to allow lazy retrieval of referenced docs
def get(self, name):

    if not hasattr(self,'_db'):
        return None
    
    col = Collection(self._db, self.collection)
    
    return getattr(SuperDoc(
        col,
        self._db[self.collection].find_one(self.id)
    ), name)

DBRef.__getattr__ = get

class Collection:
    """Represents all methods a collection can have. To create a new
    document in a collection, call new().
    """
    
    
    def __init__(self, _monga_instance, doctype, echo=False):
        
        self._doctype = doctype
        self._monga = _monga_instance
        DBRef._db = _monga_instance._db
        self._echo = echo

        
    def new(self, **datas):
        """Return empty document, with preset collection.
        """
        
        return self._doctype( self._monga, **datas )


    def _parse_query(self, kwargs):
        """Parse argument list into mongo query. 
        
        Examples:
            (user='jack')  =>  {'user': 'jack'}
            (comment__user='john') => {'comment.user': 'john'}
            (comment__rating__lt=10) => {'comment.rating': {'$lt': 10}}
            (user__in=[10, 20]) => {'user': {'$in': [10, 20]}}
        """
        
        q = {}
        # iterate over kwargs and build query dict
        for k, v in kwargs.items():
            # handle query operators
            op = k.split('__')[-1]
            if op in ('lte', 'gte', 'lt', 'gt', 'ne',
                'in', 'nin', 'all', 'size', 'exists'):
                
                k = k[:k.find('__' + op)]
                
                if op == 'in':
                    v = {'$%s' % op: k == '_id' and map(lambda x: ObjectId(str(x)), v) or v }
                else:
                    v = {'$%s' % op: k == '_id' and ObjectId(str(v)) or v }
                
            if k == '_id':
                v = type(v) in (unicode,str) and ObjectId(str(v)) or v
            else:
                v = type(v) is ObjectId and str(v) or v
                
            #v = k == '_id' and  type(v) in (unicode,str) and ObjectId(str(v)) or v
            v = type(v) == list and str(v) or v
            
            # XXX dunno if we really need this?
            #if type(v) == list:
            #    v = str(v)
            
            # convert django style notation into dot notation
            key = k.replace('__', '.')
            
            # convert mongodbobject SuperDoc type to pymongo DBRef type.
            # it's necessary for pymongo search working correctly
            if type(v) == SuperDoc:
                v = DBRef(v._collection,v._id)
                
            
            q[key] = v
        return q
            
    def _parse_update(self, kwargs):
        """Parse update arguments into mongo update dict.
        
        Examples:
            (name='jack')  =>  {'name': 'jack'}
            (person__gender='male')  =>  {'person.gender': 'male'}
            (set__friends=['mike'])  =>  {'$set': {'friends': ['mike']}}
            (push__friends='john')  =>  {'$push': {'friends': 'john'}}
        """
        
        q = {}
        op_list = {}
        # iterate over kwargs
        for k, v in kwargs.items():
        
            # get modification operator
            op = k.split('__')[0]
            if op in ('inc', 'set', 'push', 'pushall', 'pull', 'pullall'):
                # pay attention to case sensitivity
                op = op.replace('pushall', 'pushAll')
                op = op.replace('pullall', 'pullAll')
                
                # remove operator from key
                k = k.replace(op + '__', '')
                
                # append values to operator list (group operators)
                if not op_list.has_key(op):
                    op_list[op] = []

                op_list[op].append((k, v))
            # simple value assignment
            else:
                q[k] = v

        # append operator dict to mongo update dict
        for k, v in op_list.items():
            et = {}
            for i in v:
                et[i[0]] = i[1]
                
            q['$' + k] = et
        
        return q
    
    def _parse_option(self, kwargs):
        
        q = {}

        for k, v in kwargs.items():
        
            op = k.split("__")[-1]
            if op in ('upsert',):
                k = "$%s" % op
                q[k] = v
                
        return q

    def query(self, **kwargs):
        """This method is used to first say which documents should be
        affected and later what to do with these documents. They can be
        removed or updated after they have been selected.
        
        c = Collection('test')
        c.query(name='jack').delete()
        c.query(name='jack').update(set__name='john')
        """
        
        class RemoveUpdateHandler(Collection):
            def __init__(self, _monga_instance, doctype, query):
                self._monga = _monga_instance
                self._doctype = doctype
                self.__query = query
        
            def remove(self, safe=False):
                try:
                    self._monga._db[self._doctype._collection_name].remove(self.__query, safe = safe)
                except:
                    return False
                return True
                
            def update(self, update, options = {}):
                
                _cond = '_id' in update and ObjectId(str(update['_id'])) or self.__query
                
                _update_param = self._parse_update(update)
                
                if self._echo is True:
                    print "update:", _update_param
                
                return self._monga._db[self._doctype._collection_name].update(
                    _cond, 
                    _update_param,
                    **options
                )
        
        if self._monga.config.get('nometaname') == False:
            # hanya hapus pada record yg memiliki model yg tepat
            # untuk menjaga terjadinya penghapusan data pada beberapa model berbeda
            # dalam satu koleksi yg sama
            kwargs['_metaname_'] = self._doctype.__name__
    
        # return handler
        _query_param = self._parse_query(kwargs)
        
        if self._echo is True:
            print "query:", _query_param
        
        rv = RemoveUpdateHandler( self._monga, self._doctype, _query_param)
        rv._echo = self._echo
        return rv
        
        
    def insert(self, doc):
        
        if type(doc) == self._doctype:
            doc.set_monga( self._monga )
            return doc.save()
        else:
            raise SuperDocError, "Invalid doc type %s inserted to %s collection." % (doc.__class__.__name__ ,self._doctype.__name__)
    
    
    def find(self, **kwargs):
        """Find documents based on query using the django query syntax.
        See _parse_query() for details.
        """
        
        if self._monga.config.get('nometaname') == False:
            # hanya untuk record yg memiliki model yg tepat
            # untuk menjaga terjadinya pencampuran data pada beberapa model berbeda
            # dalam satu koleksi yg sama
            kwargs['_metaname_'] = self._doctype.__name__
        
        _cond = self._parse_query(kwargs)
        
        if self._echo is True:
            print 'find cond:', _cond
        
        return SuperDocList(
            DocList(
                self._monga,
                self._doctype, 
                self._monga._db[self._doctype._collection_name].find( _cond )
            )
        )
        
    # thanks to andrew trusty
    def find_one(self, **kwargs):
        """Find one single document. Mainly this is used to retrieve
        documents by unique key.
        """

        if self._monga.config.get('nometaname') == False:
            kwargs['_metaname_'] = self._doctype.__name__
            
        _cond = self._parse_query(kwargs)

        docs = self._monga._db[self._doctype._collection_name].find_one( _cond )

        if docs is None:
            return None

        return self._doctype( self._monga, **dict(map(lambda x: (str(x[0]), x[1]), docs.items())) )
        
        
    def count(self, **kwargs):
        '''Nggo ngolehake jumlah record nang njero koleksi secara shortcut
        '''
        return self.find( **kwargs ).count()
        
    def ensure_index( self, key, ttl=600, unique=False ):
        '''nggo ngawe index nek perlu
        '''
        return self._monga._db[self._doctype._collection_name].ensure_index(key, ttl = ttl, unique = unique)
        
        
    def map_reduce( self, map_func, reduce_func ):
        
        map_func = Code(map_func.replace('\n',''))
        reduce_func = Code(reduce_func.replace('\n',''))
        
        return self._monga._db[self._doctype._collection_name].map_reduce(map_func, reduce_func)
        
        
    def clear( self ):
        '''nggo ngapus kabeh data record neng collection
        '''
        return self._monga._db[self._doctype._collection_name].remove({})
        
        
        
