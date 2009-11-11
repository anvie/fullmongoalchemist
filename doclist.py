from antypes import dictarg

class DocList:
    """Represents a list of documents that are iteratable. 
    Objectifying the documents is lazy. Every doc gets converted to 
    an object if it's requested through the iterator.
    """
    
    
    def __init__(self, db, doctype, items):
        """Initialize DocList using the collection it belongs to and
        the items as iterator.
        """
        
        self._items = items
        self._db = db
        self._doctype = doctype
    
    def __iter__(self):
        """Iterator
        """
        
        return self
    
    def skip(self, num):
        """Skip 'num' docs starting at the beginning.
        """
    
        return DocList(self._db, self._doctype, self._items.skip(num))
        
    def limit(self, num):
        """Limit result list to 'num' docs.
        """
        
        return DocList(self._db, self._doctype, self._items.limit(num))
        
    def sort(self, **kwargs):
        """Sort result on key.
        
        sort(name=1, person__gender=1)  =>  {'name': 1, 'person.gender': 1}
        """
        
        sort = [(k.replace('__', '.'), v) for k, v in kwargs.items()]
        return DocList(self._db, self._doctype, self._items.sort(sort))
        
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
        return DocList( self._db, self._doctype, self._items.rewind() )
    
    def next(self):
        """Iterator
        """
        

        return self._doctype( self._db, **dictarg(self._items.next()) )

