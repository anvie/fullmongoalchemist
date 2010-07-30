from antypes import dictarg
from reg import mapped_user_class_docs

class DocList:
    """Represents a list of documents that are iteratable. 
    Objectifying the documents is lazy. Every doc gets converted to 
    an object if it's requested through the iterator.
    """
    
    
    def __init__(self, _monga_instance, doctype, items):
        """Initialize DocList using the collection it belongs to and
        the items as iterator.
        """
        
        self._items = items
        self._monga = _monga_instance
        self._doctype = doctype
    
    def __iter__(self):
        """Iterator
        """
        
        return self
    
    def skip(self, num):
        """Skip 'num' docs starting at the beginning.
        """
    
        return DocList(self._monga, self._doctype, self._items.skip(num))
        
    def limit(self, num):
        """Limit result list to 'num' docs.
        """
        
        return DocList(self._monga, self._doctype, self._items.limit(num))
        
    def sort(self, **kwargs):
        """Sort result on key.
        
        sort(name=1, person__gender=1)  =>  {'name': 1, 'person.gender': 1}
        """
        
        sort = [(k.replace('__', '.'), v) for k, v in kwargs.items()]
        return DocList(self._monga, self._doctype, self._items.sort(sort))
        
    def __len__(self):
        """Number of results.
        """
        
        return self.count()
        
    def count(self):
        """Number of results.
        """

        return self._items.count()
        
    def rewind(self):
        '''nggo muter walik meng item pertama maneh
        '''
        return DocList( self._monga, self._doctype, self._items.rewind() )
    
    def next(self):
        """Iterator
        """
        return self._doctype( self._monga, **dictarg(self._items.next()) )



class SuperDocList(object):
    
    
    def __init__(self, doclist, polymorphic=False):
        
        self._doclist = doclist
        self._polymorphic = polymorphic
        
    def skip(self, num):
        return SuperDocList( self._doclist.skip(num), self._polymorphic )
    
    def limit(self, num):
        return SuperDocList( self._doclist.limit(num), self._polymorphic )
        
    def sort(self, **kwargs):
        return SuperDocList( self._doclist.sort(**kwargs), self._polymorphic )
        
    def tofirst(self):
        return SuperDocList( self._doclist.rewind(), self._polymorphic )
        
    def count( self ):
        return self._doclist.count()
        
    def all(self):
        return [ x for x in self ]
        
    def first( self ):
        if self.count()>0:
            self.tofirst()
            return self.next()
        return None
        
    def __iter__(self):
        return self
        
    def next(self):
        rv = self._doclist._items.next()
        if rv and self._polymorphic:
            relc = mapped_user_class_docs[rv['_metaname_']]
            return relc( self._doclist._monga, **dictarg(rv) )
        return self._doclist._doctype( self._doclist._monga,  **dictarg(rv) )
        
    def copy(self):
        return copy.copy( self )

