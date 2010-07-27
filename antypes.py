
from pymongo.objectid import ObjectId
from exc import RelationError
from utils import parse_query
from pymongo.binary import Binary

__all__ = [
    'ObjectId', 'Binary', 'RelationError',
    'options', 'ConditionQuery', 'or_', 'and_',
    'rawcond', 'dictarg', 'RawType', 'variant'
]

class RawType(object):
    
    def __init__(self, val):
        self.val = val

class ConditionQuery(object):
    
    def __init__(self,**conds):
        self._cond = conds
        
    def update(self,conds):
        self._cond.update(conds)

    @property
    def raw(self):
        return self._cond

    @property
    def where_value(self):
        return None
    
    def __setitem__(self, k, v):
        self._cond[k] = v

    def where(self,**params):

        rv = self.apply(**params)

        return rv and { '$where': rv } or None

    def apply(self,**patch):

        rv = self.where_value
        
        for k, v in patch.iteritems():
            
            if v is not None:
                if type(rv) == str:
                    
                    rv = rv.replace( k, type(v) in [int,long] and str(v) or type(v) == ObjectId and str(repr(v.binary.encode('hex'))) or str(repr( type(v)==unicode and str(v) or v)))
                    
                elif type(rv) == dict:
                    
                    def find_replace( dict_data, key, replacement ):
                        # recursively value replacement
                        for k, v in dict_data.iteritems():
                            if type(v) == dict:
                                find_replace( v, key, replacement )
                            elif type(v) == str:
                                if v == key:
                                    if k == '_id':
                                        return ObjectId(str(replacement))
                                    dict_data[k] = type(replacement) == ObjectId and unicode(replacement) or replacement
                                    
                        return dict_data
                    
                    rv = find_replace( rv, k, v )
                    if type( rv ) == ObjectId:
                        return rv
                    
            else:
                return None
            
        return rv
            

    def __repr__(self):
        return '<%s>' % self.__class__.__name__
    
    
class or_(ConditionQuery):

    @property
    def where_value(self):

        return ' || '.join( map(lambda x: 'this.%s == %s' % x, self._cond.items()) )

    def __repr__(self):
        return '<or_ ConditionQuery [%s]>' % self.where_value


class and_(ConditionQuery):

    @property
    def where_value(self):
        
        return parse_query( self._cond )
        
    def where(self,**params):
        
        rv = self.apply(**params)

        return rv


    def __repr__(self):
        return '<and_ ConditionQuery [%s]>' % self.where_value
    
    
class rawcond(ConditionQuery):
    
    
    @property
    def where_value(self):
        
        return parse_query( self._cond )
        

    def __repr__(self):
        return '<or_ ConditionQuery [%s]>' % self.where_value
    

class options(list):
    
    def __call__(self, value):
        '''berguna untuk mengisi data dan konversi
        '''
        if value not in self:
            raise TypeError, "Cannot assign value `%s`. Accept only `%s`" % (value, str(self))
        self.value = value
        return value
    
    def __init__(self,*args):
        list.__init__(self,args)
        self.value = None


class variant(object):
    pass
    
    
def dictarg(data):
    return dict(map(lambda x: (str(x[0]), x[1]), data.items()))


if __name__ == '__main__':
    
    
    import unittest
    
    class test(unittest.TestCase):
        
        def test_rawcond(self):
            
            cond = rawcond(name__in=':namatamu')
            tamu = ['cat','bird','wind']
            
            self.assertEqual( cond.where(namatamu=tamu), {'$where': {'name': {'$in': ['cat', 'bird', 'wind']}}} )
            
            
        def test_where_stringcond(self):
            
            cond = or_(name=':name',age=':age')
            
            self.assertEqual( cond.where(name='anvie',age=15), {'$where': "this.age == 15 || this.name == 'anvie'"} )
            
    
    suite = unittest.TestLoader().loadTestsFromTestCase(test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    
    
    

