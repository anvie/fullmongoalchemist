class Nested(object):
    """Nested represents a dumb object, that converts a given dict 
    to internal attributes. There are several ways to map a dict to
    an object.
    
    This one is based on my question at stackoverflow:
    http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
    """
    
    
    def __init__(self, d={}):
        """Convert dict to class attributes.
        """
        
        for a, b in d.items():
            # handle lists and tuples
            if isinstance(b, (list, tuple)):
                setattr(self, a, 
                    [Nested(x) if isinstance(x, dict) else x for x in b])
            # the rest
            else:
                setattr(self, a, Nested(b) if isinstance(b, dict) else b)
                
                
    def __getitem__(self, k):
        return getattr(self, k)
        
    def __getattr__(self, k):
        rv = None
        try:
            rv = object.__getattribute__(self, k)
        except:
            pass
        return rv
    
    def _hasattr(self, k):
        return k.startswith('__') == False and k in dir(self)
    
