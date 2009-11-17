from pymongo.dbref import DBRef
from pymongo.objectid import ObjectId
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
    
    
    def __init__(self, db, doctype):
        
        self._doctype = doctype
        self._db = db   
        DBRef._db = db

        
    def new(self, **datas):
        """Return empty document, with preset collection.
        """
        
        return self._doctype( self._db, **datas )


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
                v = {'$' + op: v}
                k = k[:k.find('__' + op)]
            
            # XXX dunno if we really need this?
            if type(v) == list:
                v = str(v)
            
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
            def __init__(self, db, doctype, query):
                self._db = db
                self._doctype = doctype
                self.__query = query
        
            def remove(self):
                self._db[self._doctype._collection_name].remove(self.__query)
                
            def update(self, update, options):
                self._db[self._doctype._collection_name].update(
                    self.__query, 
                    self._parse_update(update),
                    **options
                )
                
        # hanya hapus pada record yg memiliki model yg tepat
        # untuk menjaga terjadinya penghapusan data pada beberapa model berbeda
        # dalam satu koleksi yg sama
        kwargs['_metaname_'] = self._doctype.__name__
    
        # return handler
        return RemoveUpdateHandler( self._db, self._doctype, self._parse_query(kwargs))
        
        
    def insert(self, doc):
        
        if type(doc) == self._doctype:
            doc.bind_db( self._db )
            return doc.save()
        else:
            raise SuperDocError, "Invalid doc type %s inserted to %s collection." % (doc.__class__.__name__ ,self._doctype.__name__)
    
    
    def find(self, **kwargs):
        """Find documents based on query using the django query syntax.
        See _parse_query() for details.
        """
        
        # hanya untuk record yg memiliki model yg tepat
        # untuk menjaga terjadinya pencampuran data pada beberapa model berbeda
        # dalam satu koleksi yg sama
        kwargs['_metaname_'] = self._doctype.__name__
        
        return SuperDocList(
            DocList(
                self._db,
                self._doctype, 
                self._db[self._doctype._collection_name].find(self._parse_query(kwargs))
            )
        )
        
    # thanks to andrew trusty
    def find_one(self, **kwargs):
        """Find one single document. Mainly this is used to retrieve
        documents by unique key.
        """

        if '_id' in kwargs:
            _cond = ObjectId(str(kwargs['_id']))
        else:
            kwargs['_metaname_'] = self._doctype.__name__
            _cond = self._parse_query(kwargs)

        docs = self._db[self._doctype._collection_name].find_one( _cond )

        if docs is None:
            return None

        return self._doctype( self._db, **dict(map(lambda x: (str(x[0]), x[1]), docs.items())) )
        
        
    def count(self, **kwargs):
        '''Nggo ngolehake jumlah record nang njero koleksi secara shortcut
        '''
        return self.find( **kwargs ).count()
        

#@TODO: finish this code bellow

#class SuperCollection(Collection):
#    
#    def __self__(self, db, doctype, prefilter):
#        Collection.__init__(self, db, doctype)
#        self._filter = prefilter
#        
#    def new(self):
#        raise SuperDocError, "Filtered collection not support new method"
#    
#    def _parse_query(self, kwargs):
#        rv = Collection._parse_query( self, kwargs )
#        for k, v in self._filter:
#            rv[k] = v
#        return rv
#    

    
